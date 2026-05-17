"""
Carte Folium DVF de Paris alimentée par PostgreSQL.

Comportement :
- au chargement : prix médian au m² par arrondissement ;
- au clic sur un arrondissement : zoom et affichage des sections cadastrales ;
- à fort zoom : affichage automatique du parcellaire cadastral officiel.
- à partir du zoom 18 : points d'appartements plus lisibles avec popup détaillé.

La carte lit les ventes depuis la table SQL `dvf_paris_appartements`.
Les sections cadastrales viennent du cadastre ouvert Etalab et sont mises en
cache localement après le premier téléchargement.

Exécution :
    python3 src/analyse/carte_paris.py
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path
from typing import Any, Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

import folium
import numpy as np
import pandas as pd
from branca.colormap import LinearColormap
from branca.element import Element
from folium.features import DivIcon, GeoJson, GeoJsonTooltip
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/visuals/carte_paris_dvf.html"
ARRONDISSEMENTS_CACHE = ROOT_DIR / "data/raw/arrondissements_paris.geojson"
SECTIONS_CACHE_DIR = ROOT_DIR / "data/raw/cadastre_sections_paris"

ARRONDISSEMENTS_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
    "arrondissements/exports/geojson?lang=fr&timezone=Europe%2FParis"
)
SECTIONS_URL_TEMPLATE = (
    "https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/"
    "communes/75/{code_commune}/cadastre-{code_commune}-sections.json.gz"
)
PARCELLAIRE_WMS_URL = "https://data.geopf.fr/wms-r/ows"

PARIS_CENTER = [48.8566, 2.3522]
ARRONDISSEMENTS = range(1, 21)
PALETTE = ["#2f8f6f", "#93c35c", "#f1e85a", "#eba148", "#c83d35"]


QUERY_STATS_ARRONDISSEMENTS = text(
    """
    SELECT
        arrondissement,
        COUNT(*)::INTEGER AS nb_ventes,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
            AS prix_m2_median
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND arrondissement BETWEEN 1 AND 20
    GROUP BY arrondissement
    ORDER BY arrondissement;
    """
)

QUERY_POINTS_DVF = text(
    """
    SELECT
        id_mutation,
        TO_CHAR(date_mutation, 'DD/MM/YYYY') AS date_mutation,
        arrondissement,
        longitude::FLOAT AS longitude,
        latitude::FLOAT AS latitude,
        valeur_fonciere::FLOAT AS valeur_fonciere,
        surface_reelle_bati::FLOAT AS surface_reelle_bati,
        nombre_pieces_principales::INTEGER AS nombre_pieces_principales,
        prix_m2::FLOAT AS prix_m2,
        adresse_nom_voie
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND longitude IS NOT NULL
      AND latitude IS NOT NULL
      AND arrondissement BETWEEN 1 AND 20;
    """
)


def format_int(value: float | int) -> str:
    """Formate un entier avec des espaces à la française."""
    return f"{int(round(value)):,}".replace(",", " ")


def format_euros(value: float | int) -> str:
    """Formate un montant entier en euros."""
    return f"{format_int(value)}€"


def construire_engine(database_url: str | None = None) -> Engine:
    """Construit la connexion PostgreSQL à partir de l'URL ou des variables d'env."""
    if database_url:
        return create_engine(database_url)

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "12345")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    database = os.getenv("DB_NAME", "immobilier_paris")
    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )


def lire_donnees_sql(engine: Engine) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge depuis PostgreSQL les agrégats arrondissement et les points DVF."""
    with engine.connect() as conn:
        stats_arr = pd.read_sql(QUERY_STATS_ARRONDISSEMENTS, conn)
        points = pd.read_sql(QUERY_POINTS_DVF, conn)

    if stats_arr.empty:
        raise RuntimeError(
            "La table dvf_paris_appartements est vide ou ne contient aucun prix_m2."
        )

    stats_arr["arrondissement"] = stats_arr["arrondissement"].astype(int)
    points["arrondissement"] = points["arrondissement"].astype(int)
    return stats_arr, points


def charger_geojson(
    cache_path: Path,
    url: str,
    *,
    compressed: bool = False,
) -> dict[str, Any]:
    """Charge un GeoJSON depuis le cache local ou depuis son URL officielle."""
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()
    except URLError as exc:
        raise RuntimeError(
            f"Impossible de télécharger la géométrie nécessaire : {url}"
        ) from exc

    if compressed or payload[:2] == b"\x1f\x8b":
        payload = gzip.decompress(payload)

    geojson = json.loads(payload.decode("utf-8"))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as file:
        json.dump(geojson, file, ensure_ascii=False)
    return geojson


def charger_arrondissements() -> dict[str, Any]:
    """Charge les limites officielles des arrondissements parisiens."""
    return charger_geojson(ARRONDISSEMENTS_CACHE, ARRONDISSEMENTS_URL)


def charger_sections() -> dict[int, dict[str, Any]]:
    """Charge les sections cadastrales officielles, arrondissement par arrondissement."""
    sections_par_arrondissement: dict[int, dict[str, Any]] = {}

    for arrondissement in ARRONDISSEMENTS:
        code_commune = f"751{arrondissement:02d}"
        cache_path = SECTIONS_CACHE_DIR / f"cadastre-{code_commune}-sections.geojson"
        url = SECTIONS_URL_TEMPLATE.format(code_commune=code_commune)
        sections_par_arrondissement[arrondissement] = charger_geojson(
            cache_path,
            url,
            compressed=True,
        )

    return sections_par_arrondissement


def iterer_polygones(geometry: dict[str, Any]) -> Iterable[list[list[list[float]]]]:
    """Retourne les polygones d'une géométrie GeoJSON Polygon/MultiPolygon."""
    if geometry["type"] == "Polygon":
        yield geometry["coordinates"]
    elif geometry["type"] == "MultiPolygon":
        yield from geometry["coordinates"]


def points_dans_anneau(points: np.ndarray, anneau: list[list[float]]) -> np.ndarray:
    """Teste de façon vectorisée si des points (lon, lat) sont dans un anneau."""
    ring = np.asarray(anneau, dtype=float)
    if len(ring) < 4:
        return np.zeros(len(points), dtype=bool)

    x = points[:, 0]
    y = points[:, 1]
    x0, y0 = ring[:-1, 0], ring[:-1, 1]
    x1, y1 = ring[1:, 0], ring[1:, 1]

    inside = np.zeros(len(points), dtype=bool)
    for start_x, start_y, end_x, end_y in zip(x0, y0, x1, y1):
        if start_y == end_y:
            continue
        intersects = ((start_y > y) != (end_y > y)) & (
            x
            < (end_x - start_x) * (y - start_y) / (end_y - start_y) + start_x
        )
        inside ^= intersects
    return inside


def points_dans_polygone(
    points: np.ndarray, polygon_coordinates: list[list[list[float]]]
) -> np.ndarray:
    """Teste les points dans un polygone en retirant les éventuels trous."""
    inside = points_dans_anneau(points, polygon_coordinates[0])
    for trou in polygon_coordinates[1:]:
        inside &= ~points_dans_anneau(points, trou)
    return inside


def bbox_polygone(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    """Retourne min_lon, min_lat, max_lon, max_lat pour accélérer les tests."""
    coords = []
    for polygon in iterer_polygones(geometry):
        coords.extend(polygon[0])
    array = np.asarray(coords, dtype=float)
    return (
        float(array[:, 0].min()),
        float(array[:, 1].min()),
        float(array[:, 0].max()),
        float(array[:, 1].max()),
    )


def centroid_polygone(geometry: dict[str, Any]) -> tuple[float, float]:
    """Calcule un centroïde simple adapté au placement des labels de section."""
    plus_grand_anneau: np.ndarray | None = None
    plus_grande_surface = -1.0

    for polygon in iterer_polygones(geometry):
        ring = np.asarray(polygon[0], dtype=float)
        x = ring[:, 0]
        y = ring[:, 1]
        aire = abs(float(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1])))
        if aire > plus_grande_surface:
            plus_grande_surface = aire
            plus_grand_anneau = ring

    if plus_grand_anneau is None:
        return PARIS_CENTER[1], PARIS_CENTER[0]

    return (
        float(plus_grand_anneau[:, 0].mean()),
        float(plus_grand_anneau[:, 1].mean()),
    )


def attribuer_sections_aux_points(
    points: pd.DataFrame,
    sections_par_arrondissement: dict[int, dict[str, Any]],
) -> pd.DataFrame:
    """
    Associe chaque point DVF à une section cadastrale à partir de ses coordonnées.

    La table SQL actuelle n'a pas `id_parcelle`; on fait donc ici le rattachement
    spatial depuis latitude/longitude. Si `id_parcelle` est ajouté plus tard en
    base, cette étape pourra être remplacée par une agrégation SQL directe.
    """
    morceaux: list[pd.DataFrame] = []

    for arrondissement, sections in sections_par_arrondissement.items():
        points_arr = points[points["arrondissement"] == arrondissement].copy()
        if points_arr.empty:
            continue

        coords = points_arr[["longitude", "latitude"]].to_numpy(dtype=float)
        section_ids = np.full(len(points_arr), None, dtype=object)

        for feature in sections["features"]:
            geometry = feature["geometry"]
            min_lon, min_lat, max_lon, max_lat = bbox_polygone(geometry)
            candidats = (
                pd.isna(section_ids)
                & (coords[:, 0] >= min_lon)
                & (coords[:, 0] <= max_lon)
                & (coords[:, 1] >= min_lat)
                & (coords[:, 1] <= max_lat)
            )

            if not candidats.any():
                continue

            candidate_points = coords[candidats]
            inside = np.zeros(len(candidate_points), dtype=bool)
            for polygon in iterer_polygones(geometry):
                inside |= points_dans_polygone(candidate_points, polygon)

            candidate_indexes = np.flatnonzero(candidats)
            section_ids[candidate_indexes[inside]] = feature["properties"]["id"]

        points_arr["section_id"] = section_ids
        morceaux.append(points_arr.dropna(subset=["section_id"]))

    if not morceaux:
        return pd.DataFrame(columns=[*points.columns, "section_id"])

    return pd.concat(morceaux, ignore_index=True)


def calculer_stats_sections(points_sections: pd.DataFrame) -> pd.DataFrame:
    """Calcule le nombre de ventes et le prix médian au m² par section."""
    if points_sections.empty:
        return pd.DataFrame(columns=["section_id", "nb_ventes", "prix_m2_median"])

    return (
        points_sections.groupby("section_id", as_index=False)
        .agg(
            nb_ventes=("prix_m2", "size"),
            prix_m2_median=("prix_m2", "median"),
        )
        .sort_values("section_id")
    )


def enrichir_arrondissements(
    geojson: dict[str, Any],
    stats_arr: pd.DataFrame,
) -> dict[str, Any]:
    """Ajoute les statistiques SQL aux polygones d'arrondissement."""
    stats = stats_arr.set_index("arrondissement")

    for feature in geojson["features"]:
        props = feature["properties"]
        arrondissement = int(props["c_ar"])
        row = stats.loc[arrondissement]
        props.update(
            {
                "arrondissement_code": arrondissement,
                "arrondissement_label": f"Paris {arrondissement}e Arrondissement",
                "prix_m2_median": float(row["prix_m2_median"]),
                "prix_m2_median_fmt": format_euros(row["prix_m2_median"]),
                "nb_ventes": int(row["nb_ventes"]),
                "nb_ventes_fmt": format_int(row["nb_ventes"]),
            }
        )
    return geojson


def enrichir_sections(
    sections_par_arrondissement: dict[int, dict[str, Any]],
    stats_sections: pd.DataFrame,
) -> dict[int, dict[str, Any]]:
    """Ajoute les statistiques calculées aux sections cadastrales."""
    stats = stats_sections.set_index("section_id")

    for arrondissement, geojson in sections_par_arrondissement.items():
        for feature in geojson["features"]:
            props = feature["properties"]
            section_id = props["id"]
            code_section = props["code"]
            props.update(
                {
                    "arrondissement_code": arrondissement,
                    "section_label": f"Section {code_section}",
                }
            )

            if section_id not in stats.index:
                props.update(
                    {
                        "prix_m2_median": None,
                        "prix_m2_median_fmt": "Aucune vente",
                        "nb_ventes": 0,
                        "nb_ventes_fmt": "0",
                    }
                )
                continue

            row = stats.loc[section_id]
            props.update(
                {
                    "prix_m2_median": float(row["prix_m2_median"]),
                    "prix_m2_median_fmt": format_euros(row["prix_m2_median"]),
                    "nb_ventes": int(row["nb_ventes"]),
                    "nb_ventes_fmt": format_int(row["nb_ventes"]),
                }
            )

    return sections_par_arrondissement


def creer_colormap(valeurs: pd.Series, caption: str) -> LinearColormap:
    """Crée une échelle colorée verte -> rouge comparable aux captures."""
    valeurs = valeurs.dropna()
    return LinearColormap(
        colors=PALETTE,
        vmin=float(valeurs.min()),
        vmax=float(valeurs.max()),
        caption=caption,
    )


def css_carte() -> str:
    """Ajoute juste le style nécessaire aux labels de sections."""
    return """
    <style>
        .section-label {
            color: rgba(17, 24, 39, 0.72);
            font-size: 11px;
            font-weight: 700;
            text-align: center;
            text-shadow: 0 1px 2px rgba(255, 255, 255, 0.95);
            white-space: nowrap;
        }

        .appartement-popup {
            min-width: 180px;
            font-size: 13px;
            line-height: 1.45;
        }

        .appartement-popup strong {
            display: block;
            margin-bottom: 5px;
            font-size: 14px;
        }

        .appartement-popup .muted {
            color: #6b7280;
        }
    </style>
    """


def javascript_interactions(
    map_name: str,
    arrondissements_layer_name: str,
    sections_layer_names: dict[int, str],
    parcellaire_layer_name: str,
    points_appartements: pd.DataFrame,
) -> str:
    """Gère le clic arrondissement -> sections et l'affichage du parcellaire."""
    sections_js = ",\n".join(
        f'            "{arrondissement}": {layer_name}'
        for arrondissement, layer_name in sections_layer_names.items()
    )
    points_js = json.dumps(
        [
            [
                round(float(row.latitude), 6),
                round(float(row.longitude), 6),
                format_euros(row.valeur_fonciere),
                f"{float(row.surface_reelle_bati):.0f} m²",
                int(row.nombre_pieces_principales),
                format_euros(row.prix_m2),
                row.date_mutation,
                row.adresse_nom_voie,
            ]
            for row in points_appartements.itertuples(index=False)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return f"""
    <script>
        window.addEventListener("load", () => {{
            const carte = {map_name};
            const coucheArrondissements = {arrondissements_layer_name};
            const couchesSections = {{
{sections_js}
            }};
            const coucheParcellaire = {parcellaire_layer_name};
            const appartements = {points_js};
            const coucheAppartements = L.layerGroup();
            let arrondissementActif = null;

            function masquerSections() {{
                Object.values(couchesSections).forEach((couche) => {{
                    if (carte.hasLayer(couche)) {{
                        carte.removeLayer(couche);
                    }}
                }});
            }}

            function afficherSections(arrondissement, bounds) {{
                masquerSections();
                const couche = couchesSections[String(arrondissement)];
                if (couche) {{
                    couche.addTo(carte);
                }}
                arrondissementActif = String(arrondissement);
                carte.fitBounds(bounds, {{ maxZoom: 14 }});
            }}

            coucheArrondissements.eachLayer((layer) => {{
                layer.on("click", () => {{
                    afficherSections(
                        layer.feature.properties.arrondissement_code,
                        layer.getBounds()
                    );
                }});
            }});

            function mettreAJourParcellaire() {{
                if (carte.getZoom() >= 17) {{
                    if (carte.hasLayer(coucheArrondissements)) {{
                        carte.removeLayer(coucheArrondissements);
                    }}
                    masquerSections();
                    if (!carte.hasLayer(coucheParcellaire)) {{
                        coucheParcellaire.addTo(carte);
                    }}
                }} else {{
                    if (!carte.hasLayer(coucheArrondissements)) {{
                        coucheArrondissements.addTo(carte);
                    }}
                    if (carte.hasLayer(coucheParcellaire)) {{
                        carte.removeLayer(coucheParcellaire);
                    }}
                    if (carte.getZoom() <= 11) {{
                        arrondissementActif = null;
                        masquerSections();
                    }} else if (arrondissementActif) {{
                        masquerSections();
                        couchesSections[arrondissementActif].addTo(carte);
                    }}
                }}
            }}

            function echapperHtml(value) {{
                return String(value ?? "")
                    .replaceAll("&", "&amp;")
                    .replaceAll("<", "&lt;")
                    .replaceAll(">", "&gt;")
                    .replaceAll('"', "&quot;")
                    .replaceAll("'", "&#039;");
            }}

            function popupAppartement(point) {{
                const [lat, lon, prix, surface, pieces, prixM2, date, adresse] = point;
                return `
                    <div class="appartement-popup">
                        <strong>Appartement</strong>
                        <div><b>Prix :</b> ${{echapperHtml(prix)}}</div>
                        <div><b>Surface :</b> ${{echapperHtml(surface)}}</div>
                        <div><b>Pièces :</b> ${{echapperHtml(pieces)}}</div>
                        <div><b>Prix au m² :</b> ${{echapperHtml(prixM2)}}</div>
                        <div class="muted">${{echapperHtml(date)}} · ${{echapperHtml(adresse)}}</div>
                    </div>
                `;
            }}

            function mettreAJourAppartements() {{
                coucheAppartements.clearLayers();
                if (carte.getZoom() < 18) {{
                    if (carte.hasLayer(coucheAppartements)) {{
                        carte.removeLayer(coucheAppartements);
                    }}
                    return;
                }}

                const bounds = carte.getBounds();
                appartements.forEach((point) => {{
                    const [lat, lon] = point;
                    if (!bounds.contains([lat, lon])) {{
                        return;
                    }}
                    L.circleMarker([lat, lon], {{
                        radius: 7,
                        color: "#ffffff",
                        weight: 2,
                        fillColor: "#b81f6f",
                        fillOpacity: 0.95,
                    }})
                        .bindPopup(popupAppartement(point))
                        .addTo(coucheAppartements);
                }});

                if (!carte.hasLayer(coucheAppartements)) {{
                    coucheAppartements.addTo(carte);
                }}
            }}

            carte.on("zoomend", mettreAJourParcellaire);
            carte.on("zoomend", mettreAJourAppartements);
            carte.on("moveend", mettreAJourAppartements);
            mettreAJourParcellaire();
            mettreAJourAppartements();
        }});
    </script>
    """


def creer_carte(
    stats_arr: pd.DataFrame,
    points: pd.DataFrame,
    arrondissements: dict[str, Any],
    sections_par_arrondissement: dict[int, dict[str, Any]],
    output_path: Path,
) -> Path:
    """Construit la carte Folium finale."""
    points_sections = attribuer_sections_aux_points(points, sections_par_arrondissement)
    stats_sections = calculer_stats_sections(points_sections)

    arrondissements = enrichir_arrondissements(arrondissements, stats_arr)
    sections_par_arrondissement = enrichir_sections(
        sections_par_arrondissement,
        stats_sections,
    )

    colormap_arr = creer_colormap(
        stats_arr["prix_m2_median"],
        "Prix médian au m²",
    )
    colormap_sections = creer_colormap(
        stats_sections["prix_m2_median"],
        "Prix médian au m²",
    )

    carte = folium.Map(
        location=PARIS_CENTER,
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
        zoom_control=True,
        prefer_canvas=True,
    )

    couche_arrondissements = GeoJson(
        arrondissements,
        name="Arrondissements",
        style_function=lambda feature: {
            "fillColor": colormap_arr(feature["properties"]["prix_m2_median"]),
            "color": "#ffffff",
            "weight": 2,
            "fillOpacity": 0.78,
        },
        highlight_function=lambda _feature: {
            "weight": 3,
            "color": "#ffffff",
            "fillOpacity": 0.92,
        },
        tooltip=GeoJsonTooltip(
            fields=[
                "arrondissement_label",
                "prix_m2_median_fmt",
                "nb_ventes_fmt",
            ],
            aliases=["", "", ""],
            labels=False,
            sticky=True,
        ),
    ).add_to(carte)

    section_layers: dict[int, folium.FeatureGroup] = {}
    for arrondissement, geojson in sections_par_arrondissement.items():
        groupe = folium.FeatureGroup(
            name=f"Sections {arrondissement}e",
            show=False,
            overlay=True,
            control=False,
        ).add_to(carte)

        GeoJson(
            geojson,
            name=f"Sections {arrondissement}e",
            style_function=lambda feature: {
                "fillColor": (
                    "#8f8f8f"
                    if feature["properties"]["prix_m2_median"] is None
                    else colormap_sections(feature["properties"]["prix_m2_median"])
                ),
                "color": "#ffffff",
                "weight": 2,
                "fillOpacity": 0.82,
            },
            highlight_function=lambda _feature: {
                "weight": 3,
                "color": "#ffffff",
                "fillOpacity": 0.95,
            },
            tooltip=GeoJsonTooltip(
                fields=[
                    "section_label",
                    "prix_m2_median_fmt",
                    "nb_ventes_fmt",
                ],
                aliases=["", "", ""],
                labels=False,
                sticky=True,
            ),
        ).add_to(groupe)

        for feature in geojson["features"]:
            lon, lat = centroid_polygone(feature["geometry"])
            folium.Marker(
                location=[lat, lon],
                icon=DivIcon(
                    html=(
                        '<div class="section-label">'
                        f'{feature["properties"]["code"]}'
                        "</div>"
                    )
                ),
            ).add_to(groupe)

        section_layers[arrondissement] = groupe

    parcellaire = folium.raster_layers.WmsTileLayer(
        url=PARCELLAIRE_WMS_URL,
        layers="CADASTRALPARCELS.PARCELLAIRE_EXPRESS",
        name="Parcelles cadastrales",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=False,
        show=False,
        opacity=0.8,
    ).add_to(carte)

    carte.get_root().header.add_child(Element(css_carte()))
    carte.get_root().html.add_child(
        Element(
            javascript_interactions(
                carte.get_name(),
                couche_arrondissements.get_name(),
                {
                    arrondissement: groupe.get_name()
                    for arrondissement, groupe in section_layers.items()
                },
                parcellaire.get_name(),
                points,
            )
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    carte.save(output_path)
    return output_path


def parser_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère une carte Folium DVF de Paris alimentée par SQL."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="URL SQLAlchemy PostgreSQL optionnelle.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Fichier HTML de sortie.",
    )
    return parser.parse_args()


def main() -> None:
    args = parser_arguments()
    engine = construire_engine(args.database_url)
    stats_arr, points = lire_donnees_sql(engine)
    arrondissements = charger_arrondissements()
    sections = charger_sections()
    output_path = creer_carte(
        stats_arr,
        points,
        arrondissements,
        sections,
        args.output,
    )
    print(f"Carte générée : {output_path}")


if __name__ == "__main__":
    main()

"""
Utilitaires Folium pour la carte DVF de Paris.

Comportement :
- au chargement : prix médian au m² par arrondissement ;
- au clic sur un arrondissement : zoom et affichage des sections cadastrales ;
- à fort zoom : affichage automatique du parcellaire cadastral officiel.
Les données sont fournies par l'appelant, par exemple Streamlit.
Les sections cadastrales viennent du cadastre ouvert Etalab et sont mises en
cache localement après le premier téléchargement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import folium
import numpy as np
import pandas as pd
from branca.colormap import LinearColormap
from branca.element import Element
from folium.features import DivIcon, GeoJson, GeoJsonTooltip


ROOT_DIR = Path(__file__).resolve().parents[2]
ARRONDISSEMENTS_CACHE = ROOT_DIR / "data/raw/arrondissements_paris.geojson"
SECTIONS_CACHE_DIR = ROOT_DIR / "data/raw/cadastre_sections_paris"

PARIS_CENTER = [48.8566, 2.3522]
ARRONDISSEMENTS = range(1, 21)
PALETTE = ["#2f8f6f", "#93c35c", "#f1e85a", "#eba148", "#c83d35"]


def format_int(value: float | int) -> str:
    """Formate un entier avec des espaces à la française."""
    return f"{int(round(value)):,}".replace(",", " ")


def format_euros(value: float | int) -> str:
    """Formate un montant entier en euros."""
    return f"{format_int(value)}€"


def charger_geojson(
    cache_path: Path,
) -> dict[str, Any]:
    """Charge un GeoJSON déjà présent dans les données locales du projet."""
    if not cache_path.exists():
        raise FileNotFoundError(f"GeoJSON local introuvable : {cache_path}")

    with cache_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def charger_arrondissements() -> dict[str, Any]:
    """Charge les limites officielles des arrondissements parisiens."""
    return charger_geojson(ARRONDISSEMENTS_CACHE)


def charger_sections() -> dict[int, dict[str, Any]]:
    """Charge les sections cadastrales officielles, arrondissement par arrondissement."""
    sections_par_arrondissement: dict[int, dict[str, Any]] = {}

    for arrondissement in ARRONDISSEMENTS:
        code_commune = f"751{arrondissement:02d}"
        cache_path = SECTIONS_CACHE_DIR / f"cadastre-{code_commune}-sections.geojson"
        sections_par_arrondissement[arrondissement] = charger_geojson(cache_path)

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

    Les données DVF n'ont pas `id_parcelle`; on fait donc ici le rattachement
    spatial depuis latitude/longitude. Si `id_parcelle` est ajouté plus tard,
    cette étape pourra être remplacée par une agrégation dédiée en amont.
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
    """Ajoute les statistiques fournies aux polygones d'arrondissement."""
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
    </style>
    """


def javascript_interactions(
    map_name: str,
    arrondissements_layer_name: str,
    sections_layer_names: dict[int, str],
) -> str:
    """Gère le clic arrondissement -> sections."""
    sections_js = ",\n".join(
        f'            "{arrondissement}": {layer_name}'
        for arrondissement, layer_name in sections_layer_names.items()
    )

    return f"""
    <script>
        const carte = {map_name};
        const coucheArrondissements = {arrondissements_layer_name};
        const couchesSections = {{
{sections_js}
        }};

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
        zoom_start=11,
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
            )
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    carte.save(output_path)
    return output_path

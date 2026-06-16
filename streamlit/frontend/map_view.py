from __future__ import annotations

from html import escape
from typing import Any

import folium
import pandas as pd
from branca.colormap import LinearColormap
from branca.element import MacroElement, Template
from folium.features import GeoJsonTooltip
from folium.plugins import FastMarkerCluster, MarkerCluster

from src.analyse import carte_paris
from frontend.config import PALETTE, ZOOM_POINTS
from frontend.formatting import formater_entier, formater_euros


class MasquerArrondissementsAuZoom(MacroElement):
    """Masque la couche colorée quand la carte affiche les ventes détaillées."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function() {
            const map = {{ this._parent.get_name() }};
            const arrondissementsLayer = {{ this.arrondissements_layer_name }};
            const seuilZoom = {{ this.seuil_zoom }};

            function synchroniserCouleurs() {
                if (map.getZoom() >= seuilZoom) {
                    map.removeLayer(arrondissementsLayer);
                } else if (!map.hasLayer(arrondissementsLayer)) {
                    map.addLayer(arrondissementsLayer);
                }
            }

            map.on("zoomend", synchroniserCouleurs);
            synchroniserCouleurs();
        })();
        {% endmacro %}
        """
    )

    def __init__(self, arrondissements_layer_name: str, seuil_zoom: int) -> None:
        super().__init__()
        self.arrondissements_layer_name = arrondissements_layer_name
        self.seuil_zoom = seuil_zoom


def extraire_vue_carte(etat: dict[str, Any] | None) -> tuple[list[float], int]:
    if not etat:
        return list(carte_paris.PARIS_CENTER), 12

    centre = etat.get("center") or {}
    lat = centre.get("lat", carte_paris.PARIS_CENTER[0])
    lon = centre.get("lng", carte_paris.PARIS_CENTER[1])
    zoom = int(etat.get("zoom") or 12)
    return [float(lat), float(lon)], zoom


def extraire_bounds(etat: dict[str, Any] | None) -> dict[str, float]:
    if not etat or not etat.get("bounds"):
        return {}

    bounds = etat["bounds"]
    sud_ouest = bounds.get("_southWest", {})
    nord_est = bounds.get("_northEast", {})
    valeurs = {
        "min_lat": sud_ouest.get("lat"),
        "max_lat": nord_est.get("lat"),
        "min_lon": sud_ouest.get("lng"),
        "max_lon": nord_est.get("lng"),
    }
    return {cle: float(valeur) for cle, valeur in valeurs.items() if valeur is not None}


def creer_carte_adresse(
    latitude: float,
    longitude: float,
    adresse: str,
    proximite: dict[str, Any] | None = None,
) -> folium.Map:
    carte = folium.Map(
        location=[latitude, longitude],
        zoom_start=16,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    rayon_metres = int((proximite or {}).get("rayon_metres") or 500)
    folium.Circle(
        location=[latitude, longitude],
        radius=rayon_metres,
        color="#dc2626",
        fill=True,
        fill_color="#dc2626",
        fill_opacity=0.06,
        weight=2,
        tooltip=f"Rayon de {rayon_metres} m",
    ).add_to(carte)
    folium.Marker(
        location=[latitude, longitude],
        tooltip=adresse,
        popup=folium.Popup(adresse, max_width=280),
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(carte)

    groupes = {
        "transport": (
            MarkerCluster(name="Transports").add_to(carte),
            "blue",
            "bus",
        ),
        "commerce": (
            MarkerCluster(name="Commerces").add_to(carte),
            "green",
            "shopping-cart",
        ),
        "education": (
            MarkerCluster(name="Écoles").add_to(carte),
            "orange",
            "graduation-cap",
        ),
        "sante": (
            MarkerCluster(name="Santé").add_to(carte),
            "purple",
            "plus",
        ),
    }
    lieux = [
        *((proximite or {}).get("transports") or []),
        *((proximite or {}).get("equipements") or []),
    ]
    for lieu in lieux:
        categorie = lieu.get("categorie")
        if categorie not in groupes:
            continue

        groupe, couleur, icone = groupes[categorie]
        lignes = ", ".join(lieu.get("lignes") or [])
        details = escape(str(lieu.get("sous_categorie") or ""))
        if lignes:
            details = f"{details}<br>Lignes : {escape(lignes)}"
        popup = (
            f"<strong>{escape(str(lieu.get('nom') or 'Lieu'))}</strong><br>"
            f"{details}<br>Distance : {int(lieu.get('distance_metres') or 0)} m"
        )
        folium.Marker(
            location=[lieu["latitude"], lieu["longitude"]],
            tooltip=str(lieu.get("nom") or "Lieu proche"),
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(color=couleur, icon=icone, prefix="fa"),
        ).add_to(groupe)

    folium.LayerControl(collapsed=True).add_to(carte)
    return carte


def enrichir_geojson_arrondissements(
    stats_arrondissements: list[dict[str, Any]],
) -> tuple[dict[str, Any], LinearColormap | None]:
    stats = pd.DataFrame(stats_arrondissements)
    stats_index = stats.set_index("arrondissement") if not stats.empty else pd.DataFrame()
    geojson = carte_paris.charger_arrondissements()

    colormap = None
    valeurs = stats["prix_m2_median"].dropna() if not stats.empty else pd.Series()
    if not valeurs.empty:
        colormap = LinearColormap(
            colors=PALETTE,
            vmin=float(valeurs.min()),
            vmax=float(valeurs.max()),
        )

    for feature in geojson["features"]:
        props = feature["properties"]
        arrondissement = int(props["c_ar"])
        suffixe = "er" if arrondissement == 1 else "e"
        props["label"] = f"Paris {arrondissement}{suffixe}"

        if not stats.empty and arrondissement in stats_index.index:
            row = stats_index.loc[arrondissement]
            props["prix_m2_median"] = float(row["prix_m2_median"])
            props["prix_m2_median_fmt"] = formater_euros(row["prix_m2_median"])
            props["nombre_ventes_fmt"] = formater_entier(row["nombre_ventes"])
        else:
            props["prix_m2_median"] = None
            props["prix_m2_median_fmt"] = "Aucune vente"
            props["nombre_ventes_fmt"] = "0"

    return geojson, colormap


def creer_carte(
    stats_arrondissements: list[dict[str, Any]],
    points: pd.DataFrame,
    *,
    centre: list[float],
    zoom: int,
) -> folium.Map:
    carte = folium.Map(
        location=centre,
        zoom_start=zoom,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    geojson, colormap = enrichir_geojson_arrondissements(stats_arrondissements)
    arrondissements_layer = folium.FeatureGroup(
        name="Prix par arrondissement",
        show=zoom < ZOOM_POINTS,
        overlay=True,
        control=False,
    ).add_to(carte)
    folium.GeoJson(
        geojson,
        style_function=lambda feature: {
            "fillColor": (
                "#9ca3af"
                if colormap is None or feature["properties"].get("prix_m2_median") is None
                else colormap(feature["properties"]["prix_m2_median"])
            ),
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
            fields=["label", "prix_m2_median_fmt", "nombre_ventes_fmt"],
            aliases=["", "Prix médian au m² :", "Ventes :"],
            sticky=True,
        ),
    ).add_to(arrondissements_layer)

    points_layer = None
    if not points.empty:
        colonnes_points = [
            "latitude",
            "longitude",
            "date_mutation",
            "surface_reelle_bati",
            "valeur_fonciere",
            "nombre_pieces_principales",
        ]
        points_legers = points[colonnes_points]
        donnees_points = points_legers.where(pd.notna(points_legers), None).values.tolist()
        callback_points = """
        function(row) {
            const entier = (valeur) => valeur == null
                ? "—"
                : Math.round(Number(valeur)).toLocaleString("fr-FR");
            const marker = L.circleMarker([row[0], row[1]], {
                radius: 5,
                color: "#ffffff",
                weight: 1.2,
                fill: true,
                fillColor: "#030712",
                fillOpacity: 0.96
            });
            const popup = `
                <span class="sale-popup-title">Appartement vendu</span>
                <div class="sale-popup-row">
                    <span class="sale-popup-label">Date</span>
                    <span class="sale-popup-value">${row[2] ?? "—"}</span>
                </div>
                <div class="sale-popup-row">
                    <span class="sale-popup-label">Surface</span>
                    <span class="sale-popup-value">${entier(row[3])} m²</span>
                </div>
                <div class="sale-popup-row">
                    <span class="sale-popup-label">Prix</span>
                    <span class="sale-popup-value">${entier(row[4])} €</span>
                </div>
                <div class="sale-popup-row">
                    <span class="sale-popup-label">Pièces</span>
                    <span class="sale-popup-value">${entier(row[5])}</span>
                </div>
            `;
            marker.bindPopup(popup, {maxWidth: 260});
            return marker;
        }
        """
        points_layer = FastMarkerCluster(
            donnees_points,
            callback=callback_points,
            options={
                "chunkedLoading": True,
                "disableClusteringAtZoom": 17,
                "removeOutsideVisibleBounds": True,
            },
            name="Appartements vendus",
            show=zoom >= ZOOM_POINTS,
            overlay=True,
            control=False,
        )
        points_layer.add_to(carte)

    MasquerArrondissementsAuZoom(
        arrondissements_layer_name=arrondissements_layer.get_name(),
        seuil_zoom=ZOOM_POINTS,
    ).add_to(carte)

    return carte

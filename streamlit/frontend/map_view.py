from __future__ import annotations

from typing import Any

import folium
import pandas as pd
from branca.colormap import LinearColormap
from branca.element import Element
from folium.features import GeoJsonTooltip

from src.analyse import carte_paris
from frontend.config import PALETTE, ZOOM_POINTS
from frontend.formatting import formater_date, formater_entier, formater_euros


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


def popup_vente(vente: dict[str, Any]) -> folium.Popup:
    html = f"""
    <span class="sale-popup-title">Appartement vendu</span>
    <div class="sale-popup-row">
        <span class="sale-popup-label">Date</span>
        <span class="sale-popup-value">{formater_date(vente.get('date_mutation'))}</span>
    </div>
    <div class="sale-popup-row">
        <span class="sale-popup-label">Surface</span>
        <span class="sale-popup-value">{formater_entier(vente.get('surface_reelle_bati'))} m²</span>
    </div>
    <div class="sale-popup-row">
        <span class="sale-popup-label">Prix</span>
        <span class="sale-popup-value">{formater_euros(vente.get('valeur_fonciere'))}</span>
    </div>
    <div class="sale-popup-row">
        <span class="sale-popup-label">Pièces</span>
        <span class="sale-popup-value">{formater_entier(vente.get('nombre_pieces_principales'))}</span>
    </div>
    """
    return folium.Popup(html, max_width=260)


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
        points_layer = folium.FeatureGroup(
            name="Appartements vendus",
            show=zoom >= ZOOM_POINTS,
            overlay=True,
            control=False,
        )
        for vente in points.to_dict(orient="records"):
            lat = vente.get("latitude")
            lon = vente.get("longitude")
            if lat is None or lon is None:
                continue

            folium.CircleMarker(
                location=[float(lat), float(lon)],
                radius=5,
                color="#ffffff",
                weight=1.2,
                fill=True,
                fill_color="#030712",
                fill_opacity=0.96,
                popup=popup_vente(vente),
                tooltip="Appartement vendu",
            ).add_to(points_layer)

        points_layer.add_to(carte)

    points_layer_name_js = (
        f'"{points_layer.get_name()}"' if points_layer is not None else "null"
    )
    carte.get_root().html.add_child(
        Element(
            f"""
            <script>
            (function attendreCarte() {{
                const map = window["{carte.get_name()}"];
                const arrondissementsLayer = window["{arrondissements_layer.get_name()}"];
                const pointsLayerName = {points_layer_name_js};
                const pointsLayer = pointsLayerName ? window[pointsLayerName] : null;
                const seuilZoom = {ZOOM_POINTS};

                if (!map || !arrondissementsLayer || (pointsLayerName && !pointsLayer)) {{
                    window.setTimeout(attendreCarte, 50);
                    return;
                }}

                function afficher(layer) {{
                    if (layer && !map.hasLayer(layer)) {{
                        map.addLayer(layer);
                    }}
                }}

                function masquer(layer) {{
                    if (layer && map.hasLayer(layer)) {{
                        map.removeLayer(layer);
                    }}
                }}

                function synchroniserCouches() {{
                    if (map.getZoom() >= seuilZoom) {{
                        masquer(arrondissementsLayer);
                        afficher(pointsLayer);
                    }} else {{
                        afficher(arrondissementsLayer);
                        masquer(pointsLayer);
                    }}
                }}

                map.on("zoomend", synchroniserCouches);
                synchroniserCouches();
            }})();
            </script>
            """
        )
    )

    return carte

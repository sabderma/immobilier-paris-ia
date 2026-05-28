from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
from typing import Any

import folium
import pandas as pd
import requests
import streamlit as st
from branca.colormap import LinearColormap
from branca.element import Element
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium

from src.analyse import carte_paris, graphiques
from src.prediction.prediction import charger_modele, predire_prix_avec_modele


ROOT_DIR = Path(__file__).resolve().parents[1]
MODELE_PREDICTION_PATH = ROOT_DIR / "models" / "xgboost_prix_dvf.joblib"
API_BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINTS = {
    "health": "/health",
    "filtres": "/dvf/filtres",
    "stats_arrondissements": "/stats/dvf/arrondissement",
    "resume": "/stats/dvf/resume",
    "evolution": "/stats/dvf/evolution-mensuelle",
    "distribution": "/stats/dvf/distribution",
    "points": "/dvf/points",
    "csv": "/dvf/export.csv",
    "commerces": "/commerces/paris",
}
PALETTE = ["#2f8f6f", "#93c35c", "#f1e85a", "#eba148", "#c83d35"]
ZOOM_POINTS = 15
MAX_POINTS = 800


def charger_env() -> None:
    """Charge les variables du fichier .env local si elles existent."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for ligne in env_path.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue

        cle, valeur = ligne.split("=", 1)
        os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


def headers_api() -> dict[str, str]:
    charger_env()
    api_key = os.getenv("API_KEY")
    return {"X-API-Key": api_key} if api_key else {}


st.set_page_config(
    page_title="Immobilier Paris",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def tuple_params(params: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted((k, v) for k, v in params.items() if v is not None))


def api_get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=headers_api(),
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        st.error(f"Erreur API sur {path} : {exc}")
        st.stop()


def api_get_csv(path: str, params: dict[str, Any] | None = None) -> bytes:
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=headers_api(),
            timeout=120,
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as exc:
        st.error(f"Erreur API sur {path} : {exc}")
        st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def charger_filtres() -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["filtres"])


@st.cache_data(ttl=120, show_spinner=False)
def charger_stats_arrondissements(params: tuple[tuple[str, Any], ...]) -> list[dict]:
    return api_get_json(API_ENDPOINTS["stats_arrondissements"], dict(params))


@st.cache_data(ttl=120, show_spinner=False)
def charger_resume(params: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["resume"], dict(params))


@st.cache_data(ttl=120, show_spinner=False)
def charger_evolution(params: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    df = pd.DataFrame(api_get_json(API_ENDPOINTS["evolution"], dict(params)))
    if not df.empty:
        df["mois"] = pd.to_datetime(df["mois"])
    return df


@st.cache_data(ttl=120, show_spinner=False)
def charger_distribution(params: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    return pd.DataFrame(api_get_json(API_ENDPOINTS["distribution"], dict(params)))


@st.cache_data(ttl=60, show_spinner=False)
def charger_points(params: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    payload = api_get_json(API_ENDPOINTS["points"], dict(params))
    return pd.DataFrame(payload.get("data", []))


@st.cache_data(ttl=300, show_spinner=False)
def charger_csv(params: tuple[tuple[str, Any], ...]) -> bytes:
    return api_get_csv(API_ENDPOINTS["csv"], dict(params))


@st.cache_data(ttl=3600, show_spinner=False)
def charger_commerces_paris() -> pd.DataFrame:
    payload = api_get_json(API_ENDPOINTS["commerces"])
    return pd.DataFrame(payload.get("data", []))


@st.cache_resource(show_spinner=False)
def charger_modele_prediction() -> Any:
    return charger_modele(MODELE_PREDICTION_PATH)


# -----------------------------------------------------------------------------
# Formatage et UI
# -----------------------------------------------------------------------------


def formater_entier(valeur: float | int | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{int(round(valeur)):,}".replace(",", " ")


def formater_euros(valeur: float | int | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{formater_entier(valeur)} €"


def formater_decimal(valeur: float | int | None, suffixe: str = "") -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{float(valeur):.1f}".replace(".", ",") + suffixe


def formater_date(valeur: Any | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    date = pd.to_datetime(valeur, errors="coerce")
    if pd.isna(date):
        return "—"
    return date.strftime("%d/%m/%Y")


def styles() -> None:
    st.markdown(
        """
        <style>
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"] {
                background: #ffffff;
                color: #111827;
            }
            .block-container {
                max-width: none;
                width: 100%;
                box-sizing: border-box;
                overflow-x: hidden;
                padding: 0.8rem 1.25rem 1rem;
            }
            .filter-box {
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                padding: 0.8rem 1rem 0.2rem;
                margin: 0.75rem 0 1rem;
                background: #f8fafc;
            }
            [data-testid="stWidgetLabel"] p,
            [data-testid="stWidgetLabel"] label,
            [data-testid="stWidgetLabel"] span {
                color: #111827 !important;
                font-weight: 700 !important;
                opacity: 1 !important;
            }
            [data-baseweb="select"] > div {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-baseweb="select"] span,
            [data-baseweb="select"] input,
            [data-baseweb="select"] svg {
                color: #111827 !important;
                fill: #111827 !important;
            }
            [data-testid="stForm"] {
                border: 1px solid #e5e7eb;
                border-radius: 0.75rem;
                background: #ffffff;
                padding: 1rem 1.15rem 0.95rem;
                margin-top: 0.75rem;
            }
            [data-testid="stNumberInput"] [data-baseweb="input"],
            [data-testid="stNumberInput"] [data-baseweb="base-input"] {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-testid="stNumberInput"] input {
                background: #ffffff !important;
                color: #111827 !important;
                -webkit-text-fill-color: #111827 !important;
            }
            [data-testid="stNumberInput"] button {
                background: #ffffff !important;
                border-color: #cbd5e1 !important;
                color: #111827 !important;
            }
            [data-testid="stNumberInput"] button svg,
            [data-testid="stNumberInput"] button span {
                color: #111827 !important;
                fill: #111827 !important;
            }
            [data-testid="stFormSubmitButton"] button {
                background: #e11d48 !important;
                border: 1px solid #e11d48 !important;
                border-radius: 0.5rem !important;
                color: #ffffff !important;
                font-weight: 800 !important;
                padding: 0.65rem 1rem !important;
            }
            [data-testid="stFormSubmitButton"] button:hover {
                background: #be123c !important;
                border-color: #be123c !important;
                color: #ffffff !important;
            }
            [data-testid="stFormSubmitButton"] button p,
            [data-testid="stFormSubmitButton"] button span {
                color: #ffffff !important;
                opacity: 1 !important;
            }
            [data-baseweb="tab-list"] {
                border-bottom: none;
                gap: 0.55rem;
                margin: 0.75rem 0 1rem;
            }
            button[data-baseweb="tab"] {
                flex: 1 1 0;
                min-height: 64px;
                justify-content: center;
                padding: 0.75rem 0.65rem !important;
                border: 1px solid #e5e7eb !important;
                border-radius: 0.75rem !important;
                background: #f8fafc !important;
                color: #475569 !important;
                font-weight: 700 !important;
                opacity: 1 !important;
                white-space: normal !important;
            }
            button[data-baseweb="tab"] p {
                color: #475569 !important;
                font-size: 0.98rem !important;
                font-weight: 800 !important;
                line-height: 1.2 !important;
                opacity: 1 !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                background: #fff1f2 !important;
                border-color: #fb7185 !important;
                box-shadow: 0 8px 22px rgba(225, 29, 72, 0.12);
                color: #e11d48 !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] p {
                color: #e11d48 !important;
            }
            [data-testid="stDownloadButton"] button {
                background: #f3f4f6 !important;
                border: 1px solid #f3f4f6 !important;
                border-radius: 0.45rem !important;
                color: #111827 !important;
                font-weight: 500 !important;
                padding: 0.6rem 0.9rem !important;
            }
            [data-testid="stDownloadButton"] button p,
            [data-testid="stDownloadButton"] button span {
                color: #111827 !important;
                opacity: 1 !important;
            }
            [data-testid="stSlider"] [role="slider"] {
                background: #ef4444 !important;
                border-color: #ef4444 !important;
            }
            [data-testid="stSlider"] [data-testid="stTickBar"] div {
                color: #111827 !important;
            }
            .leaflet-popup-content {
                color: #111827;
                font-size: 0.9rem;
                line-height: 1.45;
            }
            .sale-popup-title {
                display: block;
                font-weight: 800;
                margin-bottom: 0.25rem;
            }
            .sale-popup-row {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                min-width: 165px;
            }
            .sale-popup-label {
                color: #475569;
                font-weight: 650;
            }
            .sale-popup-value {
                color: #111827;
                font-weight: 750;
                text-align: right;
            }
            .breadcrumb { color: #64748b; font-size: 0.88rem; margin-bottom: 0.45rem; }
            .section-title {
                color: #374151;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            .city-title {
                color: #111827;
                font-size: 2rem;
                font-weight: 750;
                margin: 0.15rem 0 0.9rem;
            }
            .metric-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                border-top: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                padding: 1rem 0;
                margin-bottom: 0.8rem;
            }
            .metric-label { color: #374151; font-size: 0.84rem; font-weight: 650; }
            .metric-value { color: #111827; font-size: 1.7rem; font-weight: 750; }
            [data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 0.6rem;
                padding: 0.85rem 0.95rem;
            }
            [data-testid="stMetric"] label,
            [data-testid="stMetric"] label p,
            [data-testid="stMetricLabel"],
            [data-testid="stMetricLabel"] p {
                color: #374151 !important;
                font-weight: 750 !important;
                opacity: 1 !important;
            }
            [data-testid="stMetricValue"],
            [data-testid="stMetricValue"] div,
            [data-testid="stMetricValue"] p {
                color: #111827 !important;
                font-weight: 800 !important;
                opacity: 1 !important;
            }
            .scope-note { color: #64748b; font-size: 0.82rem; margin-bottom: 0.9rem; }
            .chart-title {
                color: #111827;
                font-size: 0.95rem;
                font-weight: 750;
                margin: 0.8rem 0 0.15rem;
            }
            .map-note {
                color: #374151;
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 0.45rem;
                padding: 0.55rem 0.75rem;
                margin-top: 0.45rem;
                font-size: 0.86rem;
            }
            .info-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
                font-size: 0.94rem;
            }
            .info-table th {
                background: #f8fafc;
                border-bottom: 1px solid #e5e7eb;
                color: #374151;
                font-weight: 800;
                padding: 0.7rem 0.8rem;
                text-align: left;
            }
            .info-table td {
                border-bottom: 1px solid #eef2f7;
                color: #111827;
                padding: 0.68rem 0.8rem;
            }
            .info-table td:last-child {
                font-weight: 800;
            }
            .prediction-result {
                border: 1px solid #fecdd3;
                border-radius: 0.75rem;
                background: #fff1f2;
                padding: 1.1rem 1.25rem;
                margin-top: 1rem;
            }
            .prediction-label {
                color: #9f1239;
                font-size: 0.86rem;
                font-weight: 800;
                text-transform: uppercase;
            }
            .prediction-price {
                color: #111827;
                font-size: 2.15rem;
                font-weight: 850;
                margin-top: 0.2rem;
            }
            .prediction-detail {
                color: #475569;
                font-size: 0.94rem;
                margin-top: 0.25rem;
            }
            .prediction-note {
                color: #374151;
                background: #ffffff;
                border: 1px solid #fecdd3;
                border-radius: 0.55rem;
                font-size: 0.88rem;
                line-height: 1.5;
                margin-top: 0.9rem;
                padding: 0.75rem 0.85rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def afficher_filtres(options: dict[str, Any]) -> dict[str, Any]:
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1.1, 1.25, 1.4, 1.4])

    with col1:
        arrondissement = st.selectbox(
            "Arrondissement",
            ["Tous", *options["arrondissements"]],
            index=0,
        )
    with col2:
        annee_min, annee_max = st.slider(
            "Années",
            int(options["annee_min"]),
            int(options["annee_max"]),
            (int(options["annee_min"]), int(options["annee_max"])),
        )
    with col3:
        surface_min, surface_max = st.slider(
            "Surface (m²)",
            int(options["surface_min"]),
            int(options["surface_max"]),
            (int(options["surface_min"]), int(options["surface_max"])),
        )
    with col4:
        pieces = st.selectbox("Nombre de pièces", ["Toutes", *options["pieces"]])

    st.markdown("</div>", unsafe_allow_html=True)
    return {
        "arrondissement": None if arrondissement == "Tous" else arrondissement,
        "annee_min": annee_min,
        "annee_max": annee_max,
        "surface_min": surface_min,
        "surface_max": surface_max,
        "nombre_pieces": None if pieces == "Toutes" else pieces,
    }


# -----------------------------------------------------------------------------
# Carte
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Graphiques et tableau
# -----------------------------------------------------------------------------


def afficher_resume(resume: dict[str, Any], zoom: int, nb_points: int) -> None:
    st.markdown('<div class="breadcrumb">France &gt; Paris (75)</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Département</div>', unsafe_allow_html=True)
    st.markdown('<div class="city-title">Paris (75)</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="metric-grid">
            <div>
                <div class="metric-label">Nombre total de ventes</div>
                <div class="metric-value">{formater_entier(resume.get("nombre_ventes"))}</div>
            </div>
            <div>
                <div class="metric-label">Prix médian au m²</div>
                <div class="metric-value">{formater_euros(resume.get("prix_m2_median"))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if zoom < ZOOM_POINTS:
        note = (
            f"Zoomez jusqu’au niveau {ZOOM_POINTS} : les points noirs des "
            "appartements apparaîtront et les couleurs disparaîtront."
        )
    else:
        note = (
            f"{formater_entier(nb_points)} appartement(s) chargé(s). "
            "Cliquez sur un point noir pour voir la date, la surface, le prix et les pièces."
        )
    st.markdown(f'<div class="scope-note">{note}</div>', unsafe_allow_html=True)


def afficher_graphiques(evolution: pd.DataFrame, distribution: pd.DataFrame) -> None:
    if evolution.empty:
        st.info("Aucune vente ne correspond à ces filtres.")
        return

    st.markdown(
        '<div class="chart-title">Évolution du prix de vente médian au m²</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        graphiques.creer_figure_evolution(evolution, titre=""),
        config={"displayModeBar": False},
        theme=None,
    )

    if not distribution.empty:
        st.markdown(
            '<div class="chart-title">Distribution du prix de vente au m²</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            graphiques.creer_figure_distribution(distribution, titre=""),
            config={"displayModeBar": False},
            theme=None,
        )


def afficher_tableau(csv_bytes: bytes) -> None:
    tableau = pd.read_csv(BytesIO(csv_bytes))
    tableau["date_mutation"] = pd.to_datetime(tableau["date_mutation"], errors="coerce")

    st.download_button(
        "Télécharger le CSV filtré",
        data=csv_bytes,
        file_name="dvf_paris_filtre.csv",
        mime="text/csv",
    )
    st.dataframe(tableau, width="stretch", hide_index=True, height=760)


def afficher_prediction(options: dict[str, Any]) -> None:
    st.markdown("### Prédire le prix d’un appartement")

    if not MODELE_PREDICTION_PATH.exists():
        st.error(
            "Le modèle de prédiction est introuvable. Lance d’abord "
            "`python src/prediction/entrainement_xgboost_prix.py`."
        )
        return

    arrondissements = [int(a) for a in options.get("arrondissements", range(1, 21))]
    arrondissements = sorted(set(arrondissements))

    surface_min = max(1, int(options.get("surface_min", 10)))
    surface_max = max(surface_min, int(options.get("surface_max", 200)))
    surface_defaut = min(max(45, surface_min), surface_max)

    with st.form("formulaire_prediction_appartement"):
        col1, col2, col3 = st.columns(3)
        with col1:
            surface = st.number_input(
                "Surface de l’appartement (m²)",
                min_value=1.0,
                max_value=float(max(surface_max, 300)),
                value=float(surface_defaut),
                step=1.0,
            )
        with col2:
            nombre_pieces = st.number_input(
                "Nombre de pièces",
                min_value=1,
                max_value=10,
                value=2,
                step=1,
            )
        with col3:
            arrondissement = st.selectbox(
                "Arrondissement",
                arrondissements,
                index=arrondissements.index(11) if 11 in arrondissements else 0,
                format_func=lambda valeur: f"Paris {valeur}",
            )

        soumis = st.form_submit_button("Prédire le prix")

    if not soumis:
        st.info("Renseigne les paramètres de ton appartement puis lance la prédiction.")
        return

    try:
        modele = charger_modele_prediction()
        prix_estime = predire_prix_avec_modele(
            modele,
            surface=surface,
            nombre_pieces=nombre_pieces,
            arrondissement=arrondissement,
        )
    except Exception as exc:
        st.error(f"Impossible de calculer la prédiction : {exc}")
        return

    prix_m2 = prix_estime / surface if surface else None
    st.markdown(
        f"""
        <div class="prediction-result">
            <div class="prediction-label">Prix estimé</div>
            <div class="prediction-price">{formater_euros(prix_estime)}</div>
            <div class="prediction-detail">
                {formater_euros(prix_m2)} / m² pour {formater_entier(surface)} m²,
                {formater_entier(nombre_pieces)} pièce(s), Paris {arrondissement}.
            </div>
            <div class="prediction-note">
                Cette estimation de prix est basée sur plusieurs prix de biens vendus auparavant.
                Le prix d’estimation peut monter un peu ou descendre selon l’endroit, le quartier,
                les biens à proximité et d’autres critères.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def afficher_noter_endroit() -> None:
    st.markdown("### Noter votre endroit")

    commerces = charger_commerces_paris()
    if commerces.empty:
        st.info("Aucune donnée commerce disponible pour Paris.")
        return

    arrondissements = sorted(commerces["arrondissement"].astype(int).tolist())
    valeur_defaut = 11 if 11 in arrondissements else arrondissements[0]
    arrondissement = st.selectbox(
        "Choisir un arrondissement",
        arrondissements,
        index=arrondissements.index(valeur_defaut),
    )

    selection = commerces[commerces["arrondissement"].astype(int) == arrondissement]
    if selection.empty:
        st.info("Aucune information disponible pour cet arrondissement.")
        return

    donnees = selection.iloc[0]
    st.markdown(f"#### {donnees['nom_arrondissement']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Note commerces",
            formater_decimal(donnees.get("note_commerces_sur_10"), "/10"),
        )
    with col2:
        st.metric("Total commerces", formater_entier(donnees.get("total_commerces")))
    with col3:
        st.metric(
            "Commerces / 10 000 hab.",
            formater_decimal(donnees.get("commerces_pour_10000_habitants")),
        )

    tableau = pd.DataFrame(
        [
            ("Population 2010", formater_entier(donnees.get("population_2010"))),
            ("Grandes surfaces", formater_entier(donnees.get("grandes_surfaces"))),
            (
                "Commerces alimentaires",
                formater_entier(donnees.get("commerces_alimentaires")),
            ),
            (
                "Commerces spécialisés",
                formater_entier(donnees.get("commerces_specialises")),
            ),
            ("Hypermarchés", formater_entier(donnees.get("hypermarche"))),
            ("Supermarchés", formater_entier(donnees.get("supermarche"))),
            ("Supérettes", formater_entier(donnees.get("superette"))),
            ("Épiceries", formater_entier(donnees.get("epicerie"))),
            ("Boulangeries", formater_entier(donnees.get("boulangerie"))),
            (
                "Boucheries-charcuteries",
                formater_entier(donnees.get("boucherie_charcuterie")),
            ),
            ("Poissonneries", formater_entier(donnees.get("poissonnerie"))),
            ("Fleuristes", formater_entier(donnees.get("fleuriste"))),
            ("Magasins d’optique", formater_entier(donnees.get("magasin_d_optique"))),
            ("Stations-service", formater_entier(donnees.get("station_service"))),
        ],
        columns=["Information", "Valeur"],
    )
    st.markdown(
        tableau.to_html(index=False, escape=True, classes="info-table"),
        unsafe_allow_html=True,
    )
    st.caption("Source : Open data Ile-de-France, Base permanente des équipements 2012.")


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------


def verifier_api() -> bool:
    try:
        api_get_json(API_ENDPOINTS["health"])
        return True
    except requests.RequestException:
        st.error(
            "L’API n’est pas démarrée. Lance d’abord : "
            "`uvicorn api.main:app --reload`, puis relance Streamlit."
        )
        return False


def main() -> None:
    styles()
    if not verifier_api():
        st.stop()

    options = charger_filtres()
    filtres = afficher_filtres(options)
    params = tuple_params(filtres)

    (
        onglet_carte,
        onglet_tableau,
        onglet_prediction,
        onglet_noter_endroit,
        onglet_sources,
    ) = st.tabs(
        [
            "🗺️ Carte",
            "▦ Tableau",
            "⌂ Prédire appartement",
            "⌖ Noter votre endroit",
            "▣ Sources",
        ]
    )

    with onglet_carte:
        etat_carte = st.session_state.get("carte_dvf", {})
        centre, zoom = extraire_vue_carte(etat_carte)
        bounds = extraire_bounds(etat_carte)

        stats_arr = charger_stats_arrondissements(params)
        points = pd.DataFrame()
        params_points = {**filtres, "limit": MAX_POINTS}
        if zoom >= ZOOM_POINTS and bounds:
            params_points.update(bounds)
        points = charger_points(tuple_params(params_points))

        carte = creer_carte(stats_arr, points, centre=centre, zoom=zoom)

        gauche, droite = st.columns([0.34, 0.66], gap="medium")
        with droite:
            st_folium(
                carte,
                key="carte_dvf",
                height=820,
                use_container_width=True,
                returned_objects=["bounds", "center", "zoom"],
                center=tuple(centre),
                zoom=zoom,
            )
            if zoom >= ZOOM_POINTS and len(points) >= MAX_POINTS:
                st.markdown(
                    f'<div class="map-note">Affichage limité à {MAX_POINTS} points pour garder la carte fluide.</div>',
                    unsafe_allow_html=True,
                )

        resume = charger_resume(params)
        evolution = charger_evolution(params)
        distribution = charger_distribution(params)
        with gauche:
            afficher_resume(resume, zoom, len(points))
            afficher_graphiques(evolution, distribution)

    with onglet_tableau:
        afficher_tableau(charger_csv(params))

    with onglet_prediction:
        afficher_prediction(options)

    with onglet_noter_endroit:
        afficher_noter_endroit()

    with onglet_sources:
        st.markdown(
            """
            ### Sources et fonctionnement

            - Les filtres, statistiques, graphiques, points de carte et exports passent par `api/main.py`.
            - L’onglet “Noter votre endroit” utilise les commerces par arrondissement d’Open data Île-de-France.
            - La carte utilise les contours officiels chargés dans `src/analyse/carte_paris.py`.
            - La prédiction charge le modèle XGBoost entraîné dans `models/xgboost_prix_dvf.joblib`.
            - Streamlit ne fait pas de requêtes SQL directes.
            - Sous le zoom 15 : affichage coloré par arrondissement.
            - À partir du zoom 15 : les couleurs sont masquées et les points noirs des appartements s’affichent avec leurs détails au clic.
            """
        )


if __name__ == "__main__":
    main()

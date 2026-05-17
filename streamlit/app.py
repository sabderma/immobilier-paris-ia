from __future__ import annotations

from io import BytesIO
from typing import Any

import folium
import pandas as pd
import requests
import streamlit as st
from branca.colormap import LinearColormap
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium

from src.analyse import carte_paris
from src.analyse import graphiques


API_BASE_URL = "http://127.0.0.1:8000"
PALETTE = ["#2f8f6f", "#93c35c", "#f1e85a", "#eba148", "#c83d35"]


st.set_page_config(
    page_title="Immobilier Paris",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def api_get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        f"{API_BASE_URL}{path}",
        params={k: v for k, v in (params or {}).items() if v is not None},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def api_get_csv(path: str, params: dict[str, Any] | None = None) -> bytes:
    response = requests.get(
        f"{API_BASE_URL}{path}",
        params={k: v for k, v in (params or {}).items() if v is not None},
        timeout=120,
    )
    response.raise_for_status()
    return response.content


def tuple_params(params: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted((k, v) for k, v in params.items() if v is not None))


@st.cache_data(ttl=300, show_spinner=False)
def charger_filtres_api() -> dict[str, Any]:
    return api_get_json("/dvf/filtres")


@st.cache_data(ttl=120, show_spinner=False)
def charger_stats_arrondissements(params_tuple: tuple[tuple[str, Any], ...]) -> list[dict]:
    return api_get_json("/stats/dvf/arrondissement", dict(params_tuple))


@st.cache_data(ttl=120, show_spinner=False)
def charger_resume(params_tuple: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return api_get_json("/stats/dvf/resume", dict(params_tuple))


@st.cache_data(ttl=120, show_spinner=False)
def charger_evolution(params_tuple: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    df = pd.DataFrame(api_get_json("/stats/dvf/evolution-mensuelle", dict(params_tuple)))
    if not df.empty:
        df["mois"] = pd.to_datetime(df["mois"])
    return df


@st.cache_data(ttl=120, show_spinner=False)
def charger_distribution(params_tuple: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    return pd.DataFrame(api_get_json("/stats/dvf/distribution", dict(params_tuple)))


@st.cache_data(ttl=300, show_spinner=False)
def charger_tableau_csv(params_tuple: tuple[tuple[str, Any], ...]) -> bytes:
    return api_get_csv("/dvf/export.csv", dict(params_tuple))


def formater_entier(valeur: float | int | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{int(round(valeur)):,}".replace(",", " ")


def formater_euros(valeur: float | int | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{formater_entier(valeur)} €"


def afficher_styles() -> None:
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
                padding-top: 0.8rem;
                padding-bottom: 1rem;
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }
            div[data-baseweb="tab-list"] {
                display: flex;
                gap: 0.35rem;
                border-bottom: 1px solid #dbe3f0;
            }
            button[data-baseweb="tab"] {
                min-width: 12rem;
                min-height: 3rem;
                font-size: 1rem;
                font-weight: 700;
                background: #edf3fc !important;
                border-radius: 0.2rem 0.2rem 0 0;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                background: #ffffff !important;
                color: #274a96 !important;
                border-top: 2px solid #274a96;
            }
            button[data-baseweb="tab"] p {
                color: #374151 !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] p {
                color: #274a96 !important;
            }
            [data-testid="stWidgetLabel"] p {
                color: #374151 !important;
                font-weight: 650;
            }
            [data-testid="stDownloadButton"] button {
                color: #ffffff !important;
                background: #274a96 !important;
                border-color: #274a96 !important;
            }
            .filter-box {
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                padding: 0.8rem 1rem 0.2rem;
                margin: 0.75rem 0 1rem;
                background: #f8fafc;
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
                line-height: 1.1;
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
            .metric-label {
                color: #374151;
                font-size: 0.84rem;
                font-weight: 650;
                margin-bottom: 0.18rem;
            }
            .metric-value {
                color: #111827;
                font-size: 1.7rem;
                font-weight: 750;
                line-height: 1.1;
            }
            .scope-note { color: #64748b; font-size: 0.82rem; margin-bottom: 0.7rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def afficher_filtres(options: dict[str, Any]) -> dict[str, Any]:
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1.1, 1.25, 1.4, 1.4])
    with col1:
        choix_arrondissement = st.selectbox(
            "Arrondissement", ["Tous", *options["arrondissements"]], index=0
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
        choix_pieces = st.selectbox(
            "Nombre de pièces", ["Toutes", *options["pieces"]], index=0
        )
    st.markdown("</div>", unsafe_allow_html=True)
    return {
        "arrondissement": None if choix_arrondissement == "Tous" else choix_arrondissement,
        "annee_min": annee_min,
        "annee_max": annee_max,
        "surface_min": surface_min,
        "surface_max": surface_max,
        "nombre_pieces": None if choix_pieces == "Toutes" else choix_pieces,
    }


def creer_carte(
    stats_arrondissements: list[dict[str, Any]],
    *,
    center: list[float] | tuple[float, float],
    zoom: int,
) -> folium.Map:
    stats = pd.DataFrame(stats_arrondissements)
    stats_index = stats.set_index("arrondissement") if not stats.empty else pd.DataFrame()
    geojson = carte_paris.charger_arrondissements()
    colormap = None
    if not stats.empty:
        valeurs = stats["prix_m2_median"].dropna()
        colormap = LinearColormap(
            colors=PALETTE,
            vmin=float(valeurs.min()),
            vmax=float(valeurs.max()),
            caption="Prix médian au m²",
        )
    for feature in geojson["features"]:
        props = feature["properties"]
        arrondissement = int(props["c_ar"])
        props["label"] = f"Paris {arrondissement}e"
        if not stats.empty and arrondissement in stats_index.index:
            row = stats_index.loc[arrondissement]
            props["prix_m2_median"] = float(row["prix_m2_median"])
            props["prix_m2_median_fmt"] = formater_euros(row["prix_m2_median"])
            props["nombre_ventes_fmt"] = formater_entier(row["nombre_ventes"])
        else:
            props["prix_m2_median"] = None
            props["prix_m2_median_fmt"] = "Aucune vente"
            props["nombre_ventes_fmt"] = "0"
    carte = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    folium.GeoJson(
        geojson,
        style_function=lambda feature: {
            "fillColor": (
                "#9ca3af"
                if colormap is None or feature["properties"]["prix_m2_median"] is None
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
    ).add_to(carte)
    return carte


def extraire_bounds(carte_state: dict[str, Any] | None) -> dict[str, float]:
    if not carte_state or not carte_state.get("bounds"):
        return {}
    bounds = carte_state["bounds"]
    sud_ouest = bounds.get("_southWest", {})
    nord_est = bounds.get("_northEast", {})
    valeurs = {
        "min_lat": sud_ouest.get("lat"),
        "max_lat": nord_est.get("lat"),
        "min_lon": sud_ouest.get("lng"),
        "max_lon": nord_est.get("lng"),
    }
    return {cle: valeur for cle, valeur in valeurs.items() if valeur is not None}


def afficher_resume_et_graphiques(
    resume: dict[str, Any],
    evolution: pd.DataFrame,
    distribution: pd.DataFrame,
    viewport_actif: bool,
) -> None:
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
        <div class="scope-note">
            {"Graphiques recalculés sur la zone visible de la carte." if viewport_actif else "Graphiques calculés sur tout Paris."}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if evolution.empty:
        st.info("Aucune vente ne correspond à cette zone ou à ces filtres.")
    else:
        st.plotly_chart(
            graphiques.creer_figure_evolution(evolution),
            config={"displayModeBar": False},
        )
    if not distribution.empty:
        st.plotly_chart(
            graphiques.creer_figure_distribution(distribution),
            config={"displayModeBar": False},
        )


def afficher_tableau(df: pd.DataFrame) -> None:
    st.subheader("Données DVF complètes")
    st.caption(f"{formater_entier(len(df))} lignes affichées depuis l’API.")
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=760,
        column_config={
            "date_mutation": st.column_config.DateColumn("Date de mutation"),
            "valeur_fonciere": st.column_config.NumberColumn(
                "Valeur foncière", format="%.0f €"
            ),
            "prix_m2": st.column_config.NumberColumn("Prix au m²", format="%.2f €"),
            "surface_reelle_bati": st.column_config.NumberColumn(
                "Surface", format="%.0f m²"
            ),
            "longitude": st.column_config.NumberColumn("Longitude", format="%.6f"),
            "latitude": st.column_config.NumberColumn("Latitude", format="%.6f"),
        },
    )


def verifier_api() -> bool:
    try:
        api_get_json("/health")
        return True
    except requests.RequestException:
        st.error(
            "L’API n’est pas démarrée. Lance d’abord : "
            "`uvicorn api.main:app --reload`, puis relance Streamlit."
        )
        return False


def main() -> None:
    afficher_styles()
    if not verifier_api():
        st.stop()
    options = charger_filtres_api()
    filtres = afficher_filtres(options)
    params_filtres = tuple_params(filtres)
    onglet_carte, onglet_tableau, onglet_sources = st.tabs(
        ["🗺️ Carte", "▦ Tableau", "▣ Sources"]
    )

    with onglet_carte:
        stats_arr = charger_stats_arrondissements(params_filtres)
        etat_carte_precedent = st.session_state.get("carte_dvf", {})
        centre_precedent = etat_carte_precedent.get("center") or {
            "lat": carte_paris.PARIS_CENTER[0],
            "lng": carte_paris.PARIS_CENTER[1],
        }
        zoom_precedent = etat_carte_precedent.get("zoom") or 12
        centre_carte = [centre_precedent["lat"], centre_precedent["lng"]]
        carte = creer_carte(
            stats_arr,
            center=centre_carte,
            zoom=int(zoom_precedent),
        )
        gauche, droite = st.columns([0.34, 0.66], gap="medium")
        with droite:
            carte_state = st_folium(
                carte,
                key="carte_dvf",
                height=820,
                use_container_width=True,
                returned_objects=["bounds", "zoom", "center"],
                center=tuple(centre_carte),
                zoom=int(zoom_precedent),
            )
        etat_carte = carte_state or st.session_state.get("carte_dvf", {})
        bounds = extraire_bounds(etat_carte)
        params_zone = {**filtres, **bounds}
        resume = charger_resume(tuple_params(params_zone))
        evolution = charger_evolution(tuple_params(params_zone))
        distribution = charger_distribution(tuple_params(params_zone))
        with gauche:
            afficher_resume_et_graphiques(
                resume,
                evolution,
                distribution,
                viewport_actif=bool(bounds),
            )

    with onglet_tableau:
        csv_bytes = charger_tableau_csv(params_filtres)
        tableau = pd.read_csv(BytesIO(csv_bytes))
        tableau["date_mutation"] = pd.to_datetime(tableau["date_mutation"], errors="coerce")
        st.download_button(
            "Télécharger le CSV filtré",
            data=csv_bytes,
            file_name="dvf_paris_clean_2021_2025_filtre.csv",
            mime="text/csv",
        )
        afficher_tableau(tableau)

    with onglet_sources:
        st.markdown(
            """
            ### Sources et architecture

            - Les **filtres**, les **statistiques**, les **graphiques** et le **CSV affiché** passent par `api/main.py`.
            - Les graphiques utilisent les données renvoyées par l’API et les fonctions de rendu de `src/analyse/graphiques.py`.
            - La carte utilise les contours de `src/analyse/carte_paris.py`.
            - Quand la zone visible de la carte change, les appels API reçoivent les nouvelles bornes géographiques et les graphiques sont recalculés.
            """
        )


if __name__ == "__main__":
    main()

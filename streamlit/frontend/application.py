from __future__ import annotations

import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

from frontend.api_client import (
    api_get_json,
    charger_csv,
    charger_distribution,
    charger_evolution,
    charger_filtres,
    charger_points,
    charger_resume,
    charger_stats_arrondissements,
    tuple_params,
)
from frontend.config import API_ENDPOINTS, MAX_POINTS, ZOOM_POINTS
from frontend.filters import afficher_filtres
from frontend.map_view import creer_carte, extraire_bounds, extraire_vue_carte
from frontend.styles import styles
from frontend.views.location_rating import afficher_noter_endroit
from frontend.views.market import afficher_graphiques, afficher_resume, afficher_tableau
from frontend.views.prediction import afficher_prediction
from frontend.views.sources import afficher_sources_et_guide


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
        afficher_sources_et_guide()

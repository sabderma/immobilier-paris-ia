from __future__ import annotations

from typing import Any

import requests
import streamlit as st
from streamlit_folium import st_folium

from frontend.api_client import (
    api_get_json,
    charger_annonces_scraping,
    charger_comparaison_scraping_dvf_2025,
    charger_csv,
    charger_distribution,
    charger_distribution_scraping,
    charger_evolution,
    charger_filtres,
    charger_filtres_scraping,
    charger_points,
    charger_resume,
    charger_resume_scraping,
    charger_stats_arrondissements,
    charger_stats_scraping_arrondissements,
    charger_stats_scraping_sources,
    tuple_params,
)
from frontend.auth_ui import (
    afficher_menu_compte,
    afficher_page_authentification,
    utilisateur_connecte,
)
from frontend.config import API_ENDPOINTS, MAX_POINTS
from frontend.filters import afficher_filtres, afficher_filtres_annonces
from frontend.formatting import formater_entier
from frontend.map_view import creer_carte, extraire_vue_carte
from frontend.styles import styles
from frontend.views.admin import afficher_admin
from frontend.views.listings import (
    afficher_cartes_annonces,
    afficher_graphiques_annonces,
    afficher_resume_annonces,
)
from frontend.views.location_rating import afficher_noter_endroit
from frontend.views.market import afficher_graphiques, afficher_resume, afficher_tableau
from frontend.views.prediction import afficher_prediction
from frontend.views.sources import afficher_sources_et_guide


TAILLE_PAGE_ANNONCES = 10
HAUTEUR_CARTE_DVF = 720


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


@st.fragment
def afficher_carte(
    filtres: dict[str, Any],
    params: tuple[tuple[str, Any], ...],
) -> None:
    params_carte_generee = st.session_state.get("params_carte_dvf_generee")
    if params_carte_generee != params:
        st.session_state["params_carte_dvf_generee"] = None

    if st.session_state["params_carte_dvf_generee"] is None:
        with st.container(border=True):
            st.markdown(
                """
                <div class="map-welcome">
                    <h2>Bonjour !<br>Bienvenue</h2>
                    <p>
                        Suivez l’évolution des prix de l’immobilier et trouvez
                        le prix des ventes immobilières sur les 5 dernières années.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            generer_carte = st.button(
                "Générer la carte des appartements vendus",
                type="primary",
                width="stretch",
                key="generer_carte_dvf",
            )

        if not generer_carte:
            return

        st.session_state["params_carte_dvf_generee"] = params
        st.rerun(scope="fragment")

    with st.spinner("Génération de la carte des appartements vendus..."):
        stats_arr = charger_stats_arrondissements(params)
        points = charger_points(tuple_params({**filtres, "limit": MAX_POINTS}))
        centre, zoom = extraire_vue_carte(None)
        carte = creer_carte(stats_arr, points, centre=centre, zoom=zoom)

    st.markdown('<div class="dvf-map-frame-anchor"></div>', unsafe_allow_html=True)
    st_folium(
        carte,
        key="carte_dvf",
        height=HAUTEUR_CARTE_DVF,
        use_container_width=True,
        returned_objects=[],
    )
    st.markdown(
        (
            f'<div class="scope-note">{formater_entier(len(points))} appartements '
            "chargés en une fois. Ils sont regroupés à distance ; zoomez pour "
            "afficher les points noirs.</div>"
        ),
        unsafe_allow_html=True,
    )


def main() -> None:
    styles()
    if not verifier_api():
        st.stop()

    utilisateur = utilisateur_connecte()
    if not utilisateur:
        afficher_page_authentification()
        return

    options = charger_filtres()
    navigation = [
        "Carte",
        "Appartements à vendre",
        "Tableau",
        "Prédire appartement",
        "Analyser votre endroit",
        "Sources",
    ]
    vue_admin = "Admin"
    if utilisateur.get("role") in {"admin", "super_admin"}:
        navigation.append(vue_admin)
    navigation_active = st.session_state.get("navigation_principale")
    if navigation_active is not None and navigation_active not in navigation:
        st.session_state["navigation_principale"] = navigation[0]

    colonne_navigation, colonne_compte = st.columns([0.82, 0.18], gap="small")
    with colonne_navigation:
        vue_active = st.segmented_control(
            "Navigation principale",
            navigation,
            default=navigation[0],
            key="navigation_principale",
            label_visibility="collapsed",
            width="stretch",
        )
    with colonne_compte:
        afficher_menu_compte()

    if vue_active != navigation[0]:
        st.session_state["params_carte_dvf_generee"] = None

    if vue_active == navigation[1]:
        filtres_annonces = afficher_filtres_annonces(charger_filtres_scraping())
        if filtres_annonces is None:
            return

        params_annonces = tuple_params(filtres_annonces)
        if st.session_state.get("filtres_pagination_annonces") != params_annonces:
            st.session_state["filtres_pagination_annonces"] = params_annonces
            st.session_state["page_annonces"] = 1

        page_annonces = max(1, int(st.session_state.get("page_annonces", 1)))
        params_annonces_page = tuple_params(
            {
                **filtres_annonces,
                "limit": TAILLE_PAGE_ANNONCES,
                "offset": (page_annonces - 1) * TAILLE_PAGE_ANNONCES,
            }
        )
        annonces, nombre_total_annonces = charger_annonces_scraping(
            params_annonces_page
        )
        nombre_pages = max(
            1,
            (nombre_total_annonces + TAILLE_PAGE_ANNONCES - 1)
            // TAILLE_PAGE_ANNONCES,
        )
        if page_annonces > nombre_pages:
            st.session_state["page_annonces"] = nombre_pages
            st.rerun()

        gauche, droite = st.columns([0.36, 0.64], gap="medium")
        with gauche:
            afficher_resume_annonces(charger_resume_scraping(params_annonces))
            afficher_graphiques_annonces(
                charger_stats_scraping_arrondissements(params_annonces),
                charger_stats_scraping_sources(params_annonces),
                charger_distribution_scraping(params_annonces),
                charger_comparaison_scraping_dvf_2025(params_annonces),
            )
        with droite:
            afficher_cartes_annonces(
                annonces,
                page=page_annonces,
                nombre_pages=nombre_pages,
                nombre_total=nombre_total_annonces,
            )
        return

    if vue_active == navigation[3]:
        afficher_prediction(options)
        return

    if vue_active == navigation[4]:
        afficher_noter_endroit()
        return

    if vue_active == navigation[5]:
        afficher_sources_et_guide()
        return

    if vue_active == vue_admin:
        afficher_admin()
        return

    filtres = afficher_filtres(options)
    params = tuple_params(filtres)

    if vue_active == navigation[0]:
        gauche, droite = st.columns([0.34, 0.66], gap="medium")
        resume = charger_resume(params)
        evolution = charger_evolution(params)
        distribution = charger_distribution(params)
        with gauche:
            afficher_resume(resume)
            afficher_graphiques(evolution, distribution)
        with droite:
            afficher_carte(filtres, params)

    elif vue_active == navigation[2]:
        afficher_tableau(charger_csv(params))

from __future__ import annotations

from typing import Any

import streamlit as st


def afficher_filtres(options: dict[str, Any]) -> dict[str, Any]:
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

    return {
        "arrondissement": None if arrondissement == "Tous" else arrondissement,
        "annee_min": annee_min,
        "annee_max": annee_max,
        "surface_min": surface_min,
        "surface_max": surface_max,
        "nombre_pieces": None if pieces == "Toutes" else pieces,
    }


def afficher_filtres_annonces(options: dict[str, Any]) -> dict[str, Any]:
    col1, col2, col3, col4 = st.columns([1.1, 1.4, 1.15, 1.15])

    with col1:
        arrondissement = st.selectbox(
            "Arrondissement",
            ["Tous", *options["arrondissements"]],
            key="scraping_arrondissement",
        )
    with col2:
        surface_min, surface_max = st.slider(
            "Surface (m²)",
            int(options["surface_min"]),
            int(options["surface_max"]),
            (int(options["surface_min"]), int(options["surface_max"])),
            key="scraping_surface",
        )
    with col3:
        pieces = st.selectbox(
            "Nombre de pièces",
            ["Toutes", *options["pieces"]],
            key="scraping_pieces",
        )
    with col4:
        source = st.selectbox(
            "Source de l’annonce",
            ["Toutes", *options["sources"]],
            format_func=lambda valeur: valeur.title() if valeur != "Toutes" else valeur,
            key="scraping_source",
        )

    return {
        "arrondissement": None if arrondissement == "Tous" else arrondissement,
        "surface_min": surface_min,
        "surface_max": surface_max,
        "nombre_pieces": None if pieces == "Toutes" else pieces,
        "source": None if source == "Toutes" else source,
    }

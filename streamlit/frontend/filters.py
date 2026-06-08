from __future__ import annotations

from typing import Any

import streamlit as st


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

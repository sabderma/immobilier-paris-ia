from __future__ import annotations

"""Vue C17 pour afficher le marche DVF : resume, graphiques et tableau."""

from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st

from src.analyse import graphiques
from frontend.formatting import formater_entier, formater_euros


def afficher_resume(resume: dict[str, Any]) -> None:
    """Affiche les indicateurs principaux des ventes DVF."""
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

    st.markdown(
        '<div class="scope-note">Les graphiques sont calculés uniquement à partir des filtres ci-dessus.</div>',
        unsafe_allow_html=True,
    )


def afficher_graphiques(evolution: pd.DataFrame, distribution: pd.DataFrame) -> None:
    """Affiche les graphiques calcules a partir des filtres."""
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
    """Affiche le tableau DVF et propose le telechargement CSV."""
    tableau = pd.read_csv(BytesIO(csv_bytes))
    tableau["date_mutation"] = pd.to_datetime(tableau["date_mutation"], errors="coerce")

    st.download_button(
        "Télécharger le CSV filtré",
        data=csv_bytes,
        file_name="dvf_paris_filtre.csv",
        mime="text/csv",
    )
    st.dataframe(tableau, width="stretch", hide_index=True, height=760)

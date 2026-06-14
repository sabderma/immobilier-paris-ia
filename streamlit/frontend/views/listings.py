from __future__ import annotations

from html import escape
from importlib import reload
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from frontend.formatting import (
    formater_date,
    formater_decimal,
    formater_entier,
    formater_euros,
)
from src.analyse import graphiques


# Streamlit conserve parfois une version partielle des modules importés pendant
# son rechargement automatique. On vérifie les fonctions réellement utilisées.
FONCTIONS_GRAPHIQUES_ANNONCES = (
    "creer_figure_prix_annonces_arrondissement",
    "creer_figure_prix_annonces_source",
    "creer_figure_distribution_prix_annonces",
    "creer_figure_comparaison_scraping_dvf_2025",
)
if any(not hasattr(graphiques, nom) for nom in FONCTIONS_GRAPHIQUES_ANNONCES):
    graphiques = reload(graphiques)


def _charger_graphiques_annonces():
    global graphiques
    if any(not hasattr(graphiques, nom) for nom in FONCTIONS_GRAPHIQUES_ANNONCES):
        graphiques = reload(graphiques)
    return graphiques


def afficher_resume_annonces(resume: dict[str, Any]) -> None:
    st.markdown('<div class="breadcrumb">France &gt; Paris (75)</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Marché des annonces</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="city-title">Appartements à vendre</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="listing-metric-grid">
            <div>
                <div class="metric-label">Annonces disponibles</div>
                <div class="metric-value">{formater_entier(resume.get("nombre_annonces"))}</div>
            </div>
            <div>
                <div class="metric-label">Prix médian</div>
                <div class="metric-value">{formater_euros(resume.get("prix_median"))}</div>
            </div>
            <div class="listing-update">
                <div class="metric-label">Prix médian au m²</div>
                <div class="metric-value">{formater_euros(resume.get("prix_m2_median"))}</div>
            </div>
            <div class="listing-update">
                <div class="metric-label">Dernière mise à jour</div>
                <div class="listing-date">{formater_date(resume.get("date_mise_a_jour"))}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="scope-note">Les annonces et graphiques suivent uniquement les filtres ci-dessus.</div>',
        unsafe_allow_html=True,
    )


def afficher_graphiques_annonces(
    stats_arrondissements: pd.DataFrame,
    stats_sources: pd.DataFrame,
    distribution: pd.DataFrame,
    comparaison_2025: pd.DataFrame,
) -> None:
    config = {"displayModeBar": False}
    graphiques_annonces = _charger_graphiques_annonces()

    if not stats_arrondissements.empty:
        st.plotly_chart(
            graphiques_annonces.creer_figure_prix_annonces_arrondissement(
                stats_arrondissements
            ),
            config=config,
            theme=None,
        )

    if not stats_sources.empty:
        st.plotly_chart(
            graphiques_annonces.creer_figure_prix_annonces_source(stats_sources),
            config=config,
            theme=None,
        )

    if not distribution.empty:
        st.plotly_chart(
            graphiques_annonces.creer_figure_distribution_prix_annonces(distribution),
            config=config,
            theme=None,
        )

    if comparaison_2025.empty:
        st.info("Aucune donnée 2025 disponible pour le comparatif scraping / DVF.")
        return

    st.plotly_chart(
        graphiques_annonces.creer_figure_comparaison_scraping_dvf_2025(comparaison_2025),
        config=config,
        theme=None,
    )


def _carte_annonce(annonce: pd.Series) -> str:
    source = escape(str(annonce.get("source", "Source inconnue")).title())
    type_bien = escape(str(annonce.get("type", "Appartement")))
    arrondissement = formater_entier(annonce.get("arrondissement"))
    return dedent(
        f"""
        <article class="listing-card">
            <div class="listing-card-top">
                <span class="listing-source">{source}</span>
                <span class="listing-date-small">{formater_date(annonce.get("date_scraping"))}</span>
            </div>
            <div class="listing-card-price">{formater_euros(annonce.get("prix"))}</div>
            <div class="listing-card-location">{type_bien} · Paris {arrondissement}</div>
            <div class="listing-card-details">
                <span><strong>{formater_decimal(annonce.get("surface"), " m²")}</strong> surface</span>
                <span><strong>{formater_entier(annonce.get("nb_pieces"))}</strong> pièce(s)</span>
                <span><strong>{formater_euros(annonce.get("prix_m2"))}</strong> / m²</span>
            </div>
        </article>
        """
    ).strip()


def afficher_cartes_annonces(
    annonces: pd.DataFrame,
    *,
    page: int,
    nombre_pages: int,
    nombre_total: int,
) -> None:
    st.markdown(
        '<div class="listing-panel-title">Annonces disponibles</div>',
        unsafe_allow_html=True,
    )
    if annonces.empty:
        st.info("Aucune annonce ne correspond à ces filtres.")
        return

    cartes = "\n".join(_carte_annonce(annonce) for _, annonce in annonces.iterrows())
    st.markdown(f'<div class="listing-grid">{cartes}</div>', unsafe_allow_html=True)
    st.caption(
        f"Page {page} sur {nombre_pages} · "
        f"{formater_entier(nombre_total)} annonces disponibles."
    )
    precedente, indicateur, suivante = st.columns([1, 1.2, 1])
    with precedente:
        if st.button(
            "Précédente",
            disabled=page <= 1,
            use_container_width=True,
            key="annonces_page_precedente",
        ):
            st.session_state["page_annonces"] = page - 1
            st.rerun()
    with indicateur:
        st.markdown(
            f'<div class="listing-pagination-info">Page {page} / {nombre_pages}</div>',
            unsafe_allow_html=True,
        )
    with suivante:
        if st.button(
            "Suivante",
            disabled=page >= nombre_pages,
            use_container_width=True,
            key="annonces_page_suivante",
        ):
            st.session_state["page_annonces"] = page + 1
            st.rerun()

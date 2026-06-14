"""
Graphiques DVF réutilisables pour l'analyse et l'interface Streamlit.

Les fonctions de construction restent indépendantes de la source des données.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


GRAPHIQUES_VERSION = 2
COULEUR_TEXTE = "#111827"
COULEUR_TEXTE_SECONDAIRE = "#64748b"
POLICE_GRAPHIQUE = {"color": COULEUR_TEXTE, "size": 11}
POLICE_TITRE = {"color": COULEUR_TEXTE, "size": 14}
POLICE_AXE = {"color": COULEUR_TEXTE_SECONDAIRE, "size": 10}


def creer_figure_evolution(
    evolution: pd.DataFrame,
    *,
    titre: str = "Évolution du prix de vente médian au m²",
) -> go.Figure:
    """Construit la courbe d'évolution mensuelle."""
    marge_haute = 38 if titre else 12
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=evolution["mois"],
            y=evolution["prix_m2_median"],
            mode="lines",
            line={"width": 2, "color": "#111827"},
            hovertemplate="<b>%{x|%b %Y}</b><br>%{y:.0f} €<extra></extra>",
        )
    )
    figure.update_layout(
        title={
            "text": titre,
            "x": 0,
            "xanchor": "left",
            "font": {"size": 16, "color": "#111827"},
        },
        margin={"l": 8, "r": 8, "t": marge_haute, "b": 8},
        height=245,
        template="plotly_white",
        font={"color": "#111827"},
        xaxis={
            "tickformat": "%b %Y",
            "showgrid": False,
            "title": "",
            "tickfont": {"size": 11, "color": "#6b7280"},
        },
        yaxis={
            "ticksuffix": " €",
            "title": "",
            "gridcolor": "#e5e7eb",
            "tickfont": {"size": 11, "color": "#6b7280"},
        },
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return figure


def creer_figure_distribution(
    distribution: pd.DataFrame,
    *,
    titre: str = "Distribution du prix de vente au m²",
) -> go.Figure:
    """Construit l'histogramme des prix au m²."""
    marge_haute = 38 if titre else 12
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=distribution["label"],
            y=distribution["nb_ventes"],
            marker={
                "color": "#bfd4fb",
                "line": {"color": "white", "width": 1.5},
            },
            hovertemplate="<b>%{x}</b><br>%{y} ventes<extra></extra>",
        )
    )
    figure.update_layout(
        title={
            "text": titre,
            "x": 0,
            "xanchor": "left",
            "font": {"size": 16, "color": "#111827"},
        },
        margin={"l": 8, "r": 8, "t": marge_haute, "b": 8},
        height=245,
        template="plotly_white",
        font={"color": "#111827"},
        xaxis={
            "title": "",
            "tickmode": "array",
            "tickvals": [
                distribution["label"].iloc[0],
                distribution["label"].iloc[-1],
            ],
            "ticktext": ["0 €", "16 000 €"],
            "showgrid": False,
            "tickfont": {"size": 11, "color": "#6b7280"},
        },
        yaxis={"title": "", "visible": False, "showgrid": False},
        bargap=0.05,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return figure


def creer_figure_prix_annonces_arrondissement(
    donnees: pd.DataFrame,
    *,
    titre: str = "Prix médian des annonces au m² par arrondissement",
) -> go.Figure:
    """Compare le prix médian au m² des annonces par arrondissement."""
    figure = go.Figure(
        go.Bar(
            x=donnees["arrondissement"].map(lambda valeur: f"Paris {int(valeur)}"),
            y=donnees["prix_m2_median"],
            marker={"color": "#fb7185"},
            customdata=donnees["nombre_annonces"],
            hovertemplate=(
                "<b>%{x}</b><br>%{y:.0f} €/m²<br>"
                "%{customdata} annonces<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title={"text": titre, "x": 0, "xanchor": "left", "font": POLICE_TITRE},
        margin={"l": 8, "r": 8, "t": 38, "b": 8},
        height=260,
        template="plotly_white",
        font=POLICE_GRAPHIQUE,
        xaxis={
            "title": "",
            "tickmode": "array",
            "tickvals": [f"Paris {valeur}" for valeur in [1, 5, 10, 15, 20]],
            "ticktext": ["Paris 1", "Paris 5", "Paris 10", "Paris 15", "Paris 20"],
            "tickangle": -25,
            "tickfont": POLICE_AXE,
            "showgrid": False,
        },
        yaxis={
            "title": "",
            "ticksuffix": " €",
            "gridcolor": "#e5e7eb",
            "tickfont": POLICE_AXE,
        },
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return figure


def creer_figure_prix_annonces_source(
    donnees: pd.DataFrame,
    *,
    titre: str = "Prix médian des annonces au m² par source",
) -> go.Figure:
    """Compare le prix médian au m² selon les sites d'annonces."""
    figure = go.Figure(
        go.Bar(
            x=donnees["source"].str.title(),
            y=donnees["prix_m2_median"],
            marker={"color": "#bfd4fb"},
            customdata=donnees["nombre_annonces"],
            hovertemplate=(
                "<b>%{x}</b><br>%{y:.0f} €/m²<br>"
                "%{customdata} annonces<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title={"text": titre, "x": 0, "xanchor": "left", "font": POLICE_TITRE},
        margin={"l": 8, "r": 8, "t": 38, "b": 8},
        height=250,
        template="plotly_white",
        font=POLICE_GRAPHIQUE,
        xaxis={
            "title": "",
            "showgrid": False,
            "tickangle": -25,
            "tickfont": POLICE_AXE,
        },
        yaxis={
            "title": "",
            "ticksuffix": " €",
            "gridcolor": "#e5e7eb",
            "tickfont": POLICE_AXE,
        },
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return figure


def creer_figure_distribution_prix_annonces(
    distribution: pd.DataFrame,
    *,
    titre: str = "Distribution du prix des annonces",
) -> go.Figure:
    """Construit la distribution des prix totaux demandés."""
    figure = go.Figure(
        go.Bar(
            x=distribution["label"],
            y=distribution["nombre_annonces"],
            marker={"color": "#fda4af", "line": {"color": "white", "width": 1}},
            hovertemplate="<b>%{x}</b><br>%{y} annonces<extra></extra>",
        )
    )
    figure.update_layout(
        title={"text": titre, "x": 0, "xanchor": "left", "font": POLICE_TITRE},
        margin={"l": 8, "r": 8, "t": 38, "b": 8},
        height=250,
        template="plotly_white",
        font=POLICE_GRAPHIQUE,
        xaxis={
            "title": "",
            "showgrid": False,
            "tickangle": -35,
            "tickfont": {"color": COULEUR_TEXTE_SECONDAIRE, "size": 9},
        },
        yaxis={"title": "", "visible": False, "showgrid": False},
        bargap=0.08,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return figure


def creer_figure_comparaison_scraping_dvf_2025(
    comparaison: pd.DataFrame,
    *,
    titre: str = "Annonces disponibles et ventes DVF 2025",
) -> go.Figure:
    """Compare les annonces disponibles avec les ventes DVF de 2025."""
    x = comparaison["arrondissement"].map(lambda valeur: f"Paris {int(valeur)}")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x,
            y=comparaison["prix_m2_scraping"],
            mode="lines+markers",
            name="Annonces disponibles",
            line={"width": 2.5, "color": "#e11d48"},
            marker={"size": 6},
            hovertemplate="<b>%{x}</b><br>%{y:.0f} €/m²<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=x,
            y=comparaison["prix_m2_dvf"],
            mode="lines+markers",
            name="Ventes DVF 2025",
            line={"width": 2.5, "color": "#2563eb"},
            marker={"size": 6},
            hovertemplate="<b>%{x}</b><br>%{y:.0f} €/m²<extra></extra>",
        )
    )
    figure.update_layout(
        title={"text": titre, "x": 0, "xanchor": "left", "font": POLICE_TITRE},
        margin={"l": 8, "r": 8, "t": 42, "b": 8},
        height=285,
        template="plotly_white",
        font=POLICE_GRAPHIQUE,
        xaxis={
            "title": "",
            "tickmode": "array",
            "tickvals": [f"Paris {valeur}" for valeur in [1, 5, 10, 15, 20]],
            "ticktext": ["Paris 1", "Paris 5", "Paris 10", "Paris 15", "Paris 20"],
            "tickangle": -25,
            "tickfont": POLICE_AXE,
            "showgrid": False,
        },
        yaxis={
            "title": "",
            "ticksuffix": " €",
            "gridcolor": "#e5e7eb",
            "tickfont": POLICE_AXE,
        },
        legend={
            "orientation": "h",
            "y": 1.13,
            "x": 0,
            "font": {"color": COULEUR_TEXTE, "size": 10},
        },
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return figure

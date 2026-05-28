"""
Graphiques DVF réutilisables pour l'analyse et l'interface Streamlit.

Les fonctions de construction restent indépendantes de la source des données.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


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

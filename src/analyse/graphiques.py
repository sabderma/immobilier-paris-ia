"""
Graphiques DVF réutilisables pour l'analyse et l'interface Streamlit.

Le module conserve les requêtes SQL du projet, mais n'exécute plus les figures
au moment de l'import. Les fonctions de construction sont ainsi utilisables par
Streamlit avec des données obtenues depuis l'API.
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


QUERY_EVOLUTION = text(
    """
    SELECT
        DATE_TRUNC('month', date_mutation) AS mois,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2) AS prix_m2_median
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND prix_m2 > 1000
      AND prix_m2 < 40000
      AND date_mutation BETWEEN '2021-01-01' AND '2025-12-31'
    GROUP BY mois
    ORDER BY mois;
    """
)

QUERY_DISTRIBUTION = text(
    """
    SELECT prix_m2
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND prix_m2 >= 0
      AND prix_m2 <= 16000
      AND date_mutation BETWEEN '2021-01-01' AND '2025-12-31';
    """
)


def construire_engine(database_url: str | None = None) -> Engine:
    """Construit une connexion PostgreSQL depuis l'URL ou les variables d'env."""
    if database_url:
        return create_engine(database_url)

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "12345")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    database = os.getenv("DB_NAME", "immobilier_paris")
    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )


def charger_evolution_sql(engine: Engine | None = None) -> pd.DataFrame:
    """Charge l'évolution mensuelle depuis PostgreSQL."""
    moteur = engine or construire_engine()
    df = pd.read_sql(QUERY_EVOLUTION, moteur)
    df["mois"] = pd.to_datetime(df["mois"], utc=True).dt.tz_convert(None)
    df["prix_m2_median"] = df["prix_m2_median"].round(0)
    return df


def charger_distribution_sql(engine: Engine | None = None) -> pd.DataFrame:
    """Charge les prix au m² nécessaires à la distribution depuis PostgreSQL."""
    moteur = engine or construire_engine()
    return pd.read_sql(QUERY_DISTRIBUTION, moteur)


def creer_distribution_depuis_prix(
    prix_m2: pd.Series,
    *,
    prix_max: int = 16000,
    pas: int = 1000,
) -> pd.DataFrame:
    """Transforme une série de prix au m² en tranches de distribution."""
    bornes = list(range(0, prix_max + pas, pas))
    categories = pd.IntervalIndex.from_breaks(bornes, closed="left")
    tranches = pd.cut(
        prix_m2.dropna(),
        bins=bornes,
        right=False,
        include_lowest=True,
    )
    distribution = (
        tranches.value_counts(sort=False)
        .reindex(categories, fill_value=0)
        .rename_axis("tranche")
        .reset_index(name="nb_ventes")
    )
    distribution["borne_min"] = distribution["tranche"].map(lambda x: int(x.left))
    distribution["borne_max"] = distribution["tranche"].map(lambda x: int(x.right))
    distribution["label"] = distribution.apply(
        lambda row: f"{row['borne_min']} € – {row['borne_max']} €",
        axis=1,
    )
    return distribution


def creer_figure_evolution(
    evolution: pd.DataFrame,
    *,
    titre: str = "Évolution du prix de vente médian au m²",
) -> go.Figure:
    """Construit la courbe d'évolution mensuelle."""
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
        title=titre,
        margin={"l": 8, "r": 8, "t": 38, "b": 8},
        height=245,
        template="plotly_white",
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
        title=titre,
        margin={"l": 8, "r": 8, "t": 38, "b": 8},
        height=245,
        template="plotly_white",
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


def main() -> None:
    """Permet de visualiser les graphiques seuls depuis la ligne de commande."""
    evolution = charger_evolution_sql()
    distribution = creer_distribution_depuis_prix(
        charger_distribution_sql()["prix_m2"]
    )
    creer_figure_evolution(evolution).show()
    creer_figure_distribution(distribution).show()


if __name__ == "__main__":
    main()

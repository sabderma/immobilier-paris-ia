from __future__ import annotations

"""Routes API C17 pour exposer les annonces immobilieres nettoyees.

Les donnees viennent surtout de la table golden_data_scraping.
"""

from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query

from api.core import (
    construire_where_dvf,
    construire_where_scraping,
    lire_sql,
    verifier_cle_api,
)


router = APIRouter()


def _where_annonces(
    arrondissement: Optional[int],
    surface_min: Optional[float],
    surface_max: Optional[float],
    nombre_pieces: Optional[int],
    source: Optional[str],
) -> tuple[str, dict[str, float | int | str]]:
    """Prepare les filtres communs aux routes d'annonces."""
    return construire_where_scraping(
        arrondissement=arrondissement,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        source=source,
    )


@router.get("/scraping/filtres")
def get_filtres_scraping(_: None = Depends(verifier_cle_api)) -> dict:
    """Retourne les filtres possibles pour les annonces."""
    # C17 : ces filtres alimentent la page "Appartements a vendre".
    stats = lire_sql(
        """
        SELECT
            MIN(surface)::FLOAT AS surface_min,
            MAX(surface)::FLOAT AS surface_max
        FROM golden_data_scraping;
        """
    ).iloc[0].to_dict()
    arrondissements = lire_sql(
        """
        SELECT DISTINCT RIGHT(localisation, 2)::INTEGER AS arrondissement
        FROM golden_data_scraping
        WHERE localisation ~ '^750(0[1-9]|1[0-9]|20)$'
        ORDER BY arrondissement;
        """
    )["arrondissement"].astype(int).tolist()
    pieces = lire_sql(
        "SELECT DISTINCT nb_pieces FROM golden_data_scraping ORDER BY nb_pieces;"
    )["nb_pieces"].astype(int).tolist()
    sources = lire_sql(
        "SELECT DISTINCT source FROM golden_data_scraping ORDER BY source;"
    )["source"].astype(str).tolist()
    return {
        **stats,
        "arrondissements": arrondissements,
        "pieces": pieces,
        "sources": sources,
    }


@router.get("/scraping/annonces")
def get_annonces_scraping(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    source: Optional[str] = None,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    """Retourne une page d'annonces avec filtres et pagination."""
    # C17 : la pagination evite d'envoyer toutes les annonces d'un coup.
    where, params = _where_annonces(
        arrondissement, surface_min, surface_max, nombre_pieces, source
    )
    nombre_total = int(
        # On compte d'abord le total pour aider le frontend a paginer.
        lire_sql(
            f"""
            SELECT COUNT(*)::INTEGER AS nombre_total
            FROM golden_data_scraping
            WHERE {where};
            """,
            params,
        ).iloc[0]["nombre_total"]
    )
    annonces = lire_sql(
        f"""
        SELECT
            id,
            source,
            type,
            prix::FLOAT AS prix,
            surface::FLOAT AS surface,
            nb_pieces,
            localisation,
            RIGHT(localisation, 2)::INTEGER AS arrondissement,
            prix_m2::FLOAT AS prix_m2,
            date_scraping::DATE::TEXT AS date_scraping
        FROM golden_data_scraping
        WHERE {where}
        ORDER BY date_scraping DESC, prix_m2 ASC, id DESC
        LIMIT :limit
        OFFSET :offset;
        """,
        {**params, "limit": limit, "offset": offset},
    )
    return {
        "nombre_resultats": len(annonces),
        "nombre_total": nombre_total,
        "limite": limit,
        "offset": offset,
        "data": annonces.to_dict(orient="records"),
    }


@router.get("/stats/scraping/resume")
def resume_scraping(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    source: Optional[str] = None,
) -> dict:
    """Retourne les indicateurs principaux des annonces."""
    where, params = _where_annonces(
        arrondissement, surface_min, surface_max, nombre_pieces, source
    )
    return lire_sql(
        f"""
        SELECT
            COUNT(*)::INTEGER AS nombre_annonces,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix)::FLOAT AS prix_median,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_median,
            MAX(date_scraping)::DATE::TEXT AS date_mise_a_jour
        FROM golden_data_scraping
        WHERE {where};
        """,
        params,
    ).iloc[0].to_dict()


@router.get("/stats/scraping/arrondissement")
def stats_scraping_arrondissement(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    source: Optional[str] = None,
) -> list[dict]:
    """Regroupe les annonces par arrondissement."""
    where, params = _where_annonces(
        arrondissement, surface_min, surface_max, nombre_pieces, source
    )
    donnees = lire_sql(
        f"""
        SELECT
            RIGHT(localisation, 2)::INTEGER AS arrondissement,
            COUNT(*)::INTEGER AS nombre_annonces,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_median
        FROM golden_data_scraping
        WHERE {where}
        GROUP BY arrondissement
        ORDER BY arrondissement;
        """,
        params,
    )
    return donnees.to_dict(orient="records")


@router.get("/stats/scraping/source")
def stats_scraping_source(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    source: Optional[str] = None,
) -> list[dict]:
    """Regroupe les annonces par source de scraping."""
    where, params = _where_annonces(
        arrondissement, surface_min, surface_max, nombre_pieces, source
    )
    donnees = lire_sql(
        f"""
        SELECT
            source,
            COUNT(*)::INTEGER AS nombre_annonces,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_median
        FROM golden_data_scraping
        WHERE {where}
        GROUP BY source
        ORDER BY nombre_annonces DESC, source;
        """,
        params,
    )
    return donnees.to_dict(orient="records")


@router.get("/stats/scraping/distribution")
def distribution_scraping(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    source: Optional[str] = None,
) -> list[dict]:
    """Construit des tranches de prix pour afficher une distribution."""
    where, params = _where_annonces(
        arrondissement, surface_min, surface_max, nombre_pieces, source
    )
    prix = lire_sql(
        f"SELECT prix::FLOAT AS prix FROM golden_data_scraping WHERE {where};",
        params,
    )["prix"]
    if prix.empty:
        return []

    bornes = list(range(0, 3_250_000, 250_000)) + [float("inf")]
    labels = [
        (
            f"{int(debut / 1000)} k€ – {int(fin / 1000)} k€"
            if fin != float("inf")
            else "3 M€ et plus"
        )
        for debut, fin in zip(bornes[:-1], bornes[1:])
    ]
    tranches = pd.cut(prix, bins=bornes, labels=labels, right=False)
    distribution = (
        tranches.value_counts(sort=False)
        .rename_axis("label")
        .reset_index(name="nombre_annonces")
    )
    distribution["label"] = distribution["label"].astype(str)
    return distribution.to_dict(orient="records")


@router.get("/stats/scraping/comparaison-dvf-2025")
def comparaison_scraping_dvf_2025(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    source: Optional[str] = None,
) -> list[dict]:
    """Compare le prix au m2 des annonces avec les ventes DVF 2025."""
    # C17 : cette route prepare les donnees deja comparees pour le graphique.
    where_scraping, params_scraping = _where_annonces(
        arrondissement, surface_min, surface_max, nombre_pieces, source
    )
    scraping = lire_sql(
        f"""
        SELECT
            RIGHT(localisation, 2)::INTEGER AS arrondissement,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_scraping
        FROM golden_data_scraping
        WHERE {where_scraping}
        GROUP BY arrondissement
        ORDER BY arrondissement;
        """,
        params_scraping,
    )

    where_dvf, params_dvf = construire_where_dvf(
        arrondissement=arrondissement,
        annee_vente=2025,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
    )
    dvf = lire_sql(
        f"""
        SELECT
            arrondissement,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_dvf
        FROM dvf_paris_appartements
        WHERE {where_dvf}
        GROUP BY arrondissement
        ORDER BY arrondissement;
        """,
        params_dvf,
    )

    comparaison = pd.merge(scraping, dvf, on="arrondissement", how="outer").sort_values(
        "arrondissement"
    )
    return [
        {
            "arrondissement": int(row["arrondissement"]),
            "prix_m2_scraping": (
                None if pd.isna(row.get("prix_m2_scraping")) else row["prix_m2_scraping"]
            ),
            "prix_m2_dvf": None if pd.isna(row.get("prix_m2_dvf")) else row["prix_m2_dvf"],
        }
        for _, row in comparaison.iterrows()
    ]

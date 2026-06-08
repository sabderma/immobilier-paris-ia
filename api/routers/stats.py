from __future__ import annotations

from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends

from api.core import construire_where_dvf, lire_sql, verifier_cle_api


router = APIRouter()


@router.get("/stats/dvf/resume")
def resume_dvf(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
) -> dict:
    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_min=annee_min,
        annee_max=annee_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )
    return lire_sql(
        f"""
        SELECT
            COUNT(*)::INTEGER AS nombre_ventes,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_median,
            AVG(valeur_fonciere)::FLOAT AS prix_moyen_vente,
            AVG(surface_reelle_bati)::FLOAT AS surface_moyenne
        FROM dvf_paris_appartements
        WHERE {where};
        """,
        params,
    ).iloc[0].to_dict()


@router.get("/stats/dvf/arrondissement")
def stats_dvf_arrondissement(
    _: None = Depends(verifier_cle_api),
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
) -> list[dict]:
    where, params = construire_where_dvf(
        annee_min=annee_min,
        annee_max=annee_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
    )
    df = lire_sql(
        f"""
        SELECT
            arrondissement,
            COUNT(*)::INTEGER AS nombre_ventes,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_median,
            AVG(valeur_fonciere)::FLOAT AS prix_moyen_vente,
            AVG(surface_reelle_bati)::FLOAT AS surface_moyenne
        FROM dvf_paris_appartements
        WHERE {where}
        GROUP BY arrondissement
        ORDER BY arrondissement;
        """,
        params,
    )
    return df.to_dict(orient="records")


@router.get("/stats/dvf/evolution-mensuelle")
def evolution_mensuelle(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
) -> list[dict]:
    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_min=annee_min,
        annee_max=annee_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )
    df = lire_sql(
        f"""
        SELECT
            DATE_TRUNC('month', date_mutation) AS mois,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2)::FLOAT
                AS prix_m2_median
        FROM dvf_paris_appartements
        WHERE {where}
          AND prix_m2 IS NOT NULL
        GROUP BY mois
        ORDER BY mois;
        """,
        params,
    )
    if not df.empty:
        df["mois"] = (
            pd.to_datetime(df["mois"], utc=True)
            .dt.tz_convert(None)
            .dt.strftime("%Y-%m-%d")
        )
        df["prix_m2_median"] = df["prix_m2_median"].round(0)
    return df.to_dict(orient="records")


@router.get("/stats/dvf/distribution")
def distribution_dvf(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
) -> list[dict]:
    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_min=annee_min,
        annee_max=annee_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )
    prix = lire_sql(
        f"""
        SELECT prix_m2
        FROM dvf_paris_appartements
        WHERE {where}
          AND prix_m2 IS NOT NULL
          AND prix_m2 >= 0
          AND prix_m2 <= 16000;
        """,
        params,
    )["prix_m2"]
    bornes = list(range(0, 17000, 1000))
    categories = pd.IntervalIndex.from_breaks(bornes, closed="left")
    tranches = pd.cut(prix, bins=bornes, right=False, include_lowest=True)
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
    return distribution.drop(columns="tranche").to_dict(orient="records")

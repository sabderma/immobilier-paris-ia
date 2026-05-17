from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


ROOT_DIR = Path(__file__).resolve().parents[1]
DVF_CSV_PATH = ROOT_DIR / "data/final/dvf_paris_clean_2021_2025.csv"


def construire_engine(database_url: str | None = None) -> Engine:
    """Construit la connexion PostgreSQL depuis l'URL ou les variables d'env."""
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


engine = construire_engine()

app = FastAPI(
    title="API Immobilier Paris",
    description="API REST pour les données immobilières de Paris",
    version="2.0.0",
)


def construire_where_dvf(
    *,
    arrondissement: int | None = None,
    annee_vente: int | None = None,
    annee_min: int | None = None,
    annee_max: int | None = None,
    mois_vente: int | None = None,
    prix_min: float | None = None,
    prix_max: float | None = None,
    prix_m2_min: float | None = None,
    prix_m2_max: float | None = None,
    surface_min: float | None = None,
    surface_max: float | None = None,
    nombre_pieces: int | None = None,
    code_postal: str | None = None,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lon: float | None = None,
    max_lon: float | None = None,
) -> tuple[str, dict[str, float | int | str]]:
    """Construit la clause WHERE SQL commune aux routes DVF."""
    conditions = ["1=1"]
    params: dict[str, float | int | str] = {}
    filtres = {
        "arrondissement": ("arrondissement = :arrondissement", arrondissement),
        "annee_vente": ("annee_vente = :annee_vente", annee_vente),
        "annee_min": ("annee_vente >= :annee_min", annee_min),
        "annee_max": ("annee_vente <= :annee_max", annee_max),
        "mois_vente": ("mois_vente = :mois_vente", mois_vente),
        "prix_min": ("valeur_fonciere >= :prix_min", prix_min),
        "prix_max": ("valeur_fonciere <= :prix_max", prix_max),
        "prix_m2_min": ("prix_m2 >= :prix_m2_min", prix_m2_min),
        "prix_m2_max": ("prix_m2 <= :prix_m2_max", prix_m2_max),
        "surface_min": ("surface_reelle_bati >= :surface_min", surface_min),
        "surface_max": ("surface_reelle_bati <= :surface_max", surface_max),
        "nombre_pieces": (
            "nombre_pieces_principales = :nombre_pieces",
            nombre_pieces,
        ),
        "code_postal": ("code_postal = :code_postal", code_postal),
        "min_lat": ("latitude >= :min_lat", min_lat),
        "max_lat": ("latitude <= :max_lat", max_lat),
        "min_lon": ("longitude >= :min_lon", min_lon),
        "max_lon": ("longitude <= :max_lon", max_lon),
    }
    for nom, (condition, valeur) in filtres.items():
        if valeur is not None:
            conditions.append(condition)
            params[nom] = valeur
    return " AND ".join(conditions), params


def lire_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    """Exécute une requête SQL et retourne un DataFrame pandas."""
    return pd.read_sql(text(query), engine, params=params or {})


@app.get("/")
def accueil() -> dict[str, str]:
    return {
        "message": "API Immobilier Paris fonctionne",
        "documentation": "http://127.0.0.1:8000/docs",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connectée"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/annonces")
def get_annonces(
    localisation: Optional[str] = None,
    type_bien: Optional[str] = Query(None, alias="type"),
    prix_min: Optional[float] = None,
    prix_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nb_pieces: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    query = """
    SELECT
        id,
        source,
        type,
        prix,
        surface,
        nb_pieces,
        localisation,
        prix_m2,
        date_scraping
    FROM golden_data_scraping
    WHERE 1=1
    """
    params = {"limit": limit, "offset": offset}

    if localisation:
        query += " AND localisation ILIKE :localisation"
        params["localisation"] = f"%{localisation}%"
    if type_bien:
        query += " AND type ILIKE :type_bien"
        params["type_bien"] = f"%{type_bien}%"
    if prix_min is not None:
        query += " AND prix >= :prix_min"
        params["prix_min"] = prix_min
    if prix_max is not None:
        query += " AND prix <= :prix_max"
        params["prix_max"] = prix_max
    if surface_min is not None:
        query += " AND surface >= :surface_min"
        params["surface_min"] = surface_min
    if surface_max is not None:
        query += " AND surface <= :surface_max"
        params["surface_max"] = surface_max
    if nb_pieces is not None:
        query += " AND nb_pieces = :nb_pieces"
        params["nb_pieces"] = nb_pieces

    query += " ORDER BY prix_m2 DESC LIMIT :limit OFFSET :offset"
    df = lire_sql(query, params)
    return {
        "nombre_resultats": len(df),
        "limit": limit,
        "offset": offset,
        "data": df.to_dict(orient="records"),
    }


@app.get("/dvf/filtres")
def get_filtres_dvf() -> dict:
    stats = lire_sql(
        """
        SELECT
            MIN(annee_vente)::INTEGER AS annee_min,
            MAX(annee_vente)::INTEGER AS annee_max,
            MIN(valeur_fonciere)::FLOAT AS prix_min,
            MAX(valeur_fonciere)::FLOAT AS prix_max,
            MIN(prix_m2)::FLOAT AS prix_m2_min,
            MAX(prix_m2)::FLOAT AS prix_m2_max,
            MIN(surface_reelle_bati)::FLOAT AS surface_min,
            MAX(surface_reelle_bati)::FLOAT AS surface_max
        FROM dvf_paris_appartements;
        """
    ).iloc[0].to_dict()
    arrondissements = lire_sql(
        "SELECT DISTINCT arrondissement FROM dvf_paris_appartements ORDER BY arrondissement;"
    )["arrondissement"].astype(int).tolist()
    pieces = lire_sql(
        """
        SELECT DISTINCT nombre_pieces_principales
        FROM dvf_paris_appartements
        ORDER BY nombre_pieces_principales;
        """
    )["nombre_pieces_principales"].astype(int).tolist()
    return {**stats, "arrondissements": arrondissements, "pieces": pieces}


@app.get("/dvf")
def get_dvf(
    arrondissement: Optional[int] = None,
    annee_vente: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    mois_vente: Optional[int] = None,
    prix_min: Optional[float] = None,
    prix_max: Optional[float] = None,
    prix_m2_min: Optional[float] = None,
    prix_m2_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    code_postal: Optional[str] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    limit: int = Query(50, ge=1, le=5000),
    offset: int = Query(0, ge=0),
) -> dict:
    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_vente=annee_vente,
        annee_min=annee_min,
        annee_max=annee_max,
        mois_vente=mois_vente,
        prix_min=prix_min,
        prix_max=prix_max,
        prix_m2_min=prix_m2_min,
        prix_m2_max=prix_m2_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        code_postal=code_postal,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )
    total = lire_sql(
        f"SELECT COUNT(*)::INTEGER AS total FROM dvf_paris_appartements WHERE {where};",
        params,
    )["total"].iloc[0]
    df = lire_sql(
        f"""
        SELECT
            id,
            id_mutation,
            date_mutation,
            annee_vente,
            mois_vente,
            valeur_fonciere,
            prix_m2,
            surface_reelle_bati,
            nombre_pieces_principales,
            type_local,
            code_postal,
            arrondissement,
            nom_commune,
            adresse_nom_voie,
            longitude,
            latitude
        FROM dvf_paris_appartements
        WHERE {where}
        ORDER BY date_mutation DESC
        LIMIT :limit OFFSET :offset;
        """,
        {**params, "limit": limit, "offset": offset},
    )
    return {
        "nombre_resultats": len(df),
        "total_resultats": int(total),
        "limit": limit,
        "offset": offset,
        "data": df.to_dict(orient="records"),
    }


@app.get("/dvf/export.csv")
def export_dvf_csv(
    arrondissement: Optional[int] = None,
    annee_vente: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    mois_vente: Optional[int] = None,
    prix_min: Optional[float] = None,
    prix_max: Optional[float] = None,
    prix_m2_min: Optional[float] = None,
    prix_m2_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    code_postal: Optional[str] = None,
) -> Response:
    aucun_filtre = all(
        valeur is None
        for valeur in [
            arrondissement,
            annee_vente,
            annee_min,
            annee_max,
            mois_vente,
            prix_min,
            prix_max,
            prix_m2_min,
            prix_m2_max,
            surface_min,
            surface_max,
            nombre_pieces,
            code_postal,
        ]
    )
    if aucun_filtre and DVF_CSV_PATH.exists():
        return Response(
            DVF_CSV_PATH.read_text(encoding="utf-8"),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    'attachment; filename="dvf_paris_clean_2021_2025.csv"'
                )
            },
        )

    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_vente=annee_vente,
        annee_min=annee_min,
        annee_max=annee_max,
        mois_vente=mois_vente,
        prix_min=prix_min,
        prix_max=prix_max,
        prix_m2_min=prix_m2_min,
        prix_m2_max=prix_m2_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        code_postal=code_postal,
    )
    df = lire_sql(
        f"""
        SELECT
            id_mutation,
            date_mutation,
            annee_vente,
            mois_vente,
            valeur_fonciere,
            prix_m2,
            surface_reelle_bati,
            nombre_pieces_principales,
            type_local,
            code_postal,
            arrondissement,
            nom_commune,
            adresse_nom_voie,
            longitude,
            latitude
        FROM dvf_paris_appartements
        WHERE {where}
        ORDER BY date_mutation DESC, id_mutation DESC;
        """,
        params,
    )
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="dvf_paris_clean_2021_2025_filtre.csv"'
            )
        },
    )


@app.get("/stats/dvf/resume")
def resume_dvf(
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


@app.get("/stats/dvf/arrondissement")
def stats_dvf_arrondissement(
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


@app.get("/stats/dvf/evolution-annuelle")
def evolution_annuelle() -> list[dict]:
    return lire_sql(
        """
        SELECT
            annee_vente,
            COUNT(*)::INTEGER AS nombre_ventes,
            AVG(valeur_fonciere)::FLOAT AS prix_moyen_vente,
            AVG(prix_m2)::FLOAT AS prix_m2_moyen
        FROM dvf_paris_appartements
        GROUP BY annee_vente
        ORDER BY annee_vente;
        """
    ).to_dict(orient="records")


@app.get("/stats/dvf/evolution-mensuelle")
def evolution_mensuelle(
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


@app.get("/stats/dvf/distribution")
def distribution_dvf(
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

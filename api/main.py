from fastapi import FastAPI, Query, HTTPException
from sqlalchemy import create_engine, text
from typing import Optional
import pandas as pd

# =========================================
# INITIALISATION API
# =========================================

app = FastAPI(
    title="API Immobilier Paris",
    description="API REST pour les données immobilières de Paris",
    version="1.0.0"
)

# =========================================
# CONNEXION POSTGRESQL
# =========================================

USER = "postgres"
PASSWORD = "12345"
HOST = "localhost"
PORT = "5433"
DATABASE = "immobilier_paris"

engine = create_engine(
    f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
)

# =========================================
# ROUTE ACCUEIL
# =========================================

@app.get("/")
def accueil():
    return {
        "message": "API Immobilier Paris fonctionne",
        "documentation": "http://127.0.0.1:8000/docs"
    }

# =========================================
# TEST CONNEXION BDD
# =========================================

@app.get("/health")
def health_check():

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connectée"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================================
# ANNONCES SCRAPING
# =========================================

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
    offset: int = Query(0, ge=0)

):

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

    params = {
        "limit": limit,
        "offset": offset
    }

    # =====================================
    # FILTRES
    # =====================================

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

    query += """
    ORDER BY prix_m2 DESC
    LIMIT :limit OFFSET :offset
    """

    df = pd.read_sql(
        text(query),
        engine,
        params=params
    )

    return {
        "nombre_resultats": len(df),
        "limit": limit,
        "offset": offset,
        "data": df.to_dict(orient="records")
    }

# =========================================
# DVF PARIS
# =========================================

@app.get("/dvf")
def get_dvf(

    arrondissement: Optional[int] = None,

    annee_vente: Optional[int] = None,
    mois_vente: Optional[int] = None,

    prix_min: Optional[float] = None,
    prix_max: Optional[float] = None,

    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,

    nombre_pieces: Optional[int] = None,

    code_postal: Optional[str] = None,

    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)

):

    query = """
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
    WHERE 1=1
    """

    params = {
        "limit": limit,
        "offset": offset
    }

    # =====================================
    # FILTRES
    # =====================================

    if arrondissement is not None:
        query += " AND arrondissement = :arrondissement"
        params["arrondissement"] = arrondissement

    if annee_vente is not None:
        query += " AND annee_vente = :annee_vente"
        params["annee_vente"] = annee_vente

    if mois_vente is not None:
        query += " AND mois_vente = :mois_vente"
        params["mois_vente"] = mois_vente

    if prix_min is not None:
        query += " AND valeur_fonciere >= :prix_min"
        params["prix_min"] = prix_min

    if prix_max is not None:
        query += " AND valeur_fonciere <= :prix_max"
        params["prix_max"] = prix_max

    if surface_min is not None:
        query += " AND surface_reelle_bati >= :surface_min"
        params["surface_min"] = surface_min

    if surface_max is not None:
        query += " AND surface_reelle_bati <= :surface_max"
        params["surface_max"] = surface_max

    if nombre_pieces is not None:
        query += """
        AND nombre_pieces_principales = :nombre_pieces
        """
        params["nombre_pieces"] = nombre_pieces

    if code_postal is not None:
        query += " AND code_postal = :code_postal"
        params["code_postal"] = code_postal

    query += """
    ORDER BY date_mutation DESC
    LIMIT :limit OFFSET :offset
    """

    df = pd.read_sql(
        text(query),
        engine,
        params=params
    )

    return {
        "nombre_resultats": len(df),
        "limit": limit,
        "offset": offset,
        "data": df.to_dict(orient="records")
    }



# =========================================
# STATS DVF PAR ARRONDISSEMENT
# =========================================

@app.get("/stats/dvf/arrondissement")
def stats_dvf_arrondissement():

    query = """
    SELECT

        arrondissement,

        COUNT(*) AS nombre_ventes,

        ROUND(AVG(valeur_fonciere), 2)
        AS prix_moyen_vente,

        ROUND(AVG(surface_reelle_bati), 2)
        AS surface_moyenne,

        ROUND(AVG(prix_m2), 2)
        AS prix_m2_moyen,

        MIN(prix_m2) AS prix_m2_min,

        MAX(prix_m2) AS prix_m2_max

    FROM dvf_paris_appartements

    GROUP BY arrondissement

    ORDER BY arrondissement;
    """

    df = pd.read_sql(text(query), engine)

    return df.to_dict(orient="records")

# =========================================
# EVOLUTION ANNUELLE DVF
# =========================================

@app.get("/stats/dvf/evolution-annuelle")
def evolution_annuelle():

    query = """
    SELECT

        annee_vente,

        COUNT(*) AS nombre_ventes,

        ROUND(AVG(valeur_fonciere), 2)
        AS prix_moyen_vente,

        ROUND(AVG(prix_m2), 2)
        AS prix_m2_moyen

    FROM dvf_paris_appartements

    GROUP BY annee_vente

    ORDER BY annee_vente;
    """

    df = pd.read_sql(text(query), engine)

    return df.to_dict(orient="records")


from __future__ import annotations

import os
from functools import lru_cache
from hmac import compare_digest
from io import StringIO
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd
import requests
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL


ROOT_DIR = Path(__file__).resolve().parents[1]
DVF_CSV_PATH = ROOT_DIR / "data/final/dvf_paris_clean_2021_2025.csv"
PREDICTION_MODEL_PATH = ROOT_DIR / "models/xgboost_prix_dvf.joblib"
COMMERCES_PARIS_API_URL = (
    "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/"
    "les-commerces-par-commune-ou-arrondissement-base-permanente-des-equipements/"
    "records"
)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
modele_prediction: Any | None = None

CHAMPS_COMMERCES = [
    "hypermarche",
    "supermarche",
    "grande_surface_de_bricolage",
    "superette",
    "epicerie",
    "boulangerie",
    "boucherie_charcuterie",
    "produits_surgeles",
    "poissonnerie",
    "librairie_papeterie_journaux",
    "magasin_de_vetements",
    "magasin_d_equipements_du_foyer",
    "magasin_de_chaussures",
    "magasin_d_electromenager_et_de_mat_audio_video",
    "magasin_de_meubles",
    "magasin_d_articles_de_sports_et_de_loisirs",
    "magasin_de_revetements_murs_et_sols",
    "droguerie_quincaillerie_bricolage",
    "parfumerie",
    "horlogerie_bijouterie",
    "fleuriste",
    "magasin_d_optique",
    "station_service",
]


def charger_env() -> None:
    """Charge les variables du fichier .env local si elles existent."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for ligne in env_path.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue

        cle, valeur = ligne.split("=", 1)
        os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


def construire_engine(database_url: str | None = None) -> Engine:
    """Construit la connexion PostgreSQL depuis l'URL ou les variables d'env."""
    charger_env()

    database_url = database_url or os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "immobilier_paris"),
    )
    return create_engine(url)


engine = construire_engine()

app = FastAPI(
    title="API Immobilier Paris",
    description="API REST pour les données immobilières de Paris",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class PredictionPrixRequest(BaseModel):
    surface: float = Field(gt=0, description="Surface du bien en m2")
    nombre_pieces: int = Field(gt=0, description="Nombre de pieces principales")
    arrondissement: int = Field(ge=1, le=20, description="Arrondissement parisien")


class PredictionPrixResponse(BaseModel):
    surface: float
    nombre_pieces: int
    arrondissement: int
    prix_estime: float
    modele: str


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


def verifier_cle_api(api_key: Optional[str] = Depends(api_key_header)) -> None:
    """Vérifie la clé API envoyée dans l'en-tête X-API-Key."""
    charger_env()
    api_key_attendue = os.getenv("API_KEY")
    if not api_key_attendue:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY n'est pas configurée sur le serveur",
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante",
        )

    if not compare_digest(api_key, api_key_attendue):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide",
        )


def charger_modele_prediction() -> Any:
    """Charge le modele XGBoost une seule fois pour les predictions API."""
    global modele_prediction

    if modele_prediction is not None:
        return modele_prediction

    if not PREDICTION_MODEL_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Modèle de prédiction introuvable. Lancez "
                "`python3 -m src.prediction.entrainement_xgboost_prix`."
            ),
        )

    modele_prediction = joblib.load(PREDICTION_MODEL_PATH)
    return modele_prediction


def predire_prix_xgboost(
    surface: float,
    nombre_pieces: int,
    arrondissement: int,
) -> float:
    modele = charger_modele_prediction()
    donnees = pd.DataFrame(
        [
            {
                "surface_reelle_bati": surface,
                "nombre_pieces_principales": nombre_pieces,
                "arrondissement": str(arrondissement),
            }
        ]
    )
    return float(modele.predict(donnees)[0])


def valeur_entier(donnees: dict[str, Any], champ: str) -> int:
    valeur = donnees.get(champ)
    if valeur is None or pd.isna(valeur):
        return 0
    return int(valeur)


def nom_arrondissement(donnees: dict[str, Any]) -> str:
    libelle = donnees.get("libelle_de_commune")
    if isinstance(libelle, list) and libelle:
        return str(libelle[0])
    if libelle:
        return str(libelle)
    numero = int(donnees.get("departement_commune", 75100)) - 75100
    suffixe = "er" if numero == 1 else "e"
    return f"Paris {numero}{suffixe} Arrondissement"


def normaliser_commerce_arrondissement(donnees: dict[str, Any]) -> dict[str, Any]:
    departement_commune = int(donnees["departement_commune"])
    population = valeur_entier(donnees, "population_2010")
    total_commerces = sum(valeur_entier(donnees, champ) for champ in CHAMPS_COMMERCES)
    commerces_pour_10000_habitants = (
        round(total_commerces / population * 10000, 1) if population else None
    )
    geo_point = donnees.get("geo_point_2d") or {}

    return {
        "arrondissement": departement_commune - 75100,
        "departement_commune": departement_commune,
        "nom_arrondissement": nom_arrondissement(donnees),
        "population_2010": population,
        "total_commerces": total_commerces,
        "commerces_pour_10000_habitants": commerces_pour_10000_habitants,
        "grandes_surfaces": sum(
            valeur_entier(donnees, champ)
            for champ in [
                "hypermarche",
                "supermarche",
                "grande_surface_de_bricolage",
            ]
        ),
        "commerces_alimentaires": sum(
            valeur_entier(donnees, champ)
            for champ in [
                "superette",
                "epicerie",
                "boulangerie",
                "boucherie_charcuterie",
                "produits_surgeles",
                "poissonnerie",
            ]
        ),
        "commerces_specialises": sum(
            valeur_entier(donnees, champ)
            for champ in [
                "librairie_papeterie_journaux",
                "magasin_de_vetements",
                "magasin_d_equipements_du_foyer",
                "magasin_de_chaussures",
                "magasin_d_electromenager_et_de_mat_audio_video",
                "magasin_de_meubles",
                "magasin_d_articles_de_sports_et_de_loisirs",
                "magasin_de_revetements_murs_et_sols",
                "droguerie_quincaillerie_bricolage",
                "parfumerie",
                "horlogerie_bijouterie",
                "fleuriste",
                "magasin_d_optique",
                "station_service",
            ]
        ),
        "hypermarche": valeur_entier(donnees, "hypermarche"),
        "supermarche": valeur_entier(donnees, "supermarche"),
        "superette": valeur_entier(donnees, "superette"),
        "epicerie": valeur_entier(donnees, "epicerie"),
        "boulangerie": valeur_entier(donnees, "boulangerie"),
        "boucherie_charcuterie": valeur_entier(donnees, "boucherie_charcuterie"),
        "poissonnerie": valeur_entier(donnees, "poissonnerie"),
        "fleuriste": valeur_entier(donnees, "fleuriste"),
        "magasin_d_optique": valeur_entier(donnees, "magasin_d_optique"),
        "station_service": valeur_entier(donnees, "station_service"),
        "lat": geo_point.get("lat"),
        "lon": geo_point.get("lon"),
    }


@lru_cache(maxsize=1)
def charger_commerces_paris() -> tuple[dict[str, Any], ...]:
    try:
        response = requests.get(
            COMMERCES_PARIS_API_URL,
            params={
                "where": "departement=75",
                "limit": 20,
                "order_by": "departement_commune",
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de récupérer les commerces parisiens",
        ) from exc

    payload = response.json()
    commerces = [
        normaliser_commerce_arrondissement(resultat)
        for resultat in payload.get("results", [])
    ]
    if not commerces:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aucune donnée commerce disponible pour Paris",
        )

    densite_max = max(
        commerce["commerces_pour_10000_habitants"] or 0 for commerce in commerces
    )
    for commerce in commerces:
        densite = commerce["commerces_pour_10000_habitants"] or 0
        commerce["note_commerces_sur_10"] = (
            round(densite / densite_max * 10, 1) if densite_max else None
        )

    return tuple(sorted(commerces, key=lambda item: item["arrondissement"]))


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


@app.post("/prediction/prix", response_model=PredictionPrixResponse)
def prediction_prix(
    payload: PredictionPrixRequest,
    _: None = Depends(verifier_cle_api),
) -> PredictionPrixResponse:
    prix_estime = predire_prix_xgboost(
        surface=payload.surface,
        nombre_pieces=payload.nombre_pieces,
        arrondissement=payload.arrondissement,
    )

    return PredictionPrixResponse(
        surface=payload.surface,
        nombre_pieces=payload.nombre_pieces,
        arrondissement=payload.arrondissement,
        prix_estime=round(prix_estime, 2),
        modele="XGBRegressor",
    )


@app.get("/commerces/paris")
def commerces_paris(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = Query(None, ge=1, le=20),
) -> dict:
    commerces = list(charger_commerces_paris())
    if arrondissement is not None:
        commerces = [
            commerce
            for commerce in commerces
            if commerce["arrondissement"] == arrondissement
        ]

    return {
        "source": "Open data Ile-de-France - Base permanente des equipements 2012",
        "nombre_resultats": len(commerces),
        "data": commerces,
    }


@app.get("/dvf/filtres")
def get_filtres_dvf(_: None = Depends(verifier_cle_api)) -> dict:
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


@app.get("/dvf/points")
def get_dvf_points(
    _: None = Depends(verifier_cle_api),
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
    limit: int = Query(800, ge=1, le=2000),
) -> dict:
    """Retourne un jeu de points léger pour l'affichage cartographique."""
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
    df = lire_sql(
        f"""
        SELECT
            date_mutation::DATE::TEXT AS date_mutation,
            arrondissement,
            valeur_fonciere,
            prix_m2,
            surface_reelle_bati,
            nombre_pieces_principales,
            longitude,
            latitude
        FROM dvf_paris_appartements
        WHERE {where}
          AND longitude IS NOT NULL
          AND latitude IS NOT NULL
        ORDER BY date_mutation DESC, id_mutation DESC
        LIMIT :limit;
        """,
        {**params, "limit": limit},
    )
    return {
        "nombre_resultats": len(df),
        "limite": limit,
        "data": df.to_dict(orient="records"),
    }


@app.get("/dvf/export.csv")
def export_dvf_csv(
    _: None = Depends(verifier_cle_api),
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


@app.get("/stats/dvf/arrondissement")
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


@app.get("/stats/dvf/evolution-mensuelle")
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


@app.get("/stats/dvf/distribution")
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

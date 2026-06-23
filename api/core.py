from __future__ import annotations

import os
from hmac import compare_digest
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL


ROOT_DIR = Path(__file__).resolve().parents[1]
DVF_CSV_PATH = ROOT_DIR / "data/final/dvf_paris_clean_2021_2025.csv"
PREDICTION_MODEL_PATH = ROOT_DIR / "models/xgboost_prix_dvf.joblib"
PREDICTION_METRICS_PATH = ROOT_DIR / "models/xgboost_prix_dvf_metrics.json"
COMMERCES_PARIS_API_URL = (
    "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/"
    "les-commerces-par-commune-ou-arrondissement-base-permanente-des-equipements/"
    "records"
)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


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
        os.environ[cle.strip()] = valeur.strip().strip('"').strip("'")


def construire_engine(database_url: str | None = None) -> Engine:
    """Construit la connexion PostgreSQL depuis l'URL ou les variables d'env."""
    charger_env()

    database_url = database_url or os.getenv("DATABASE_URL")
    if database_url:
        options: dict[str, object] = {"pool_pre_ping": True}
        if database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
            options["connect_args"] = {
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "2"))
            }
        return create_engine(database_url, **options)

    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "immobilier_paris"),
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "2"))
        },
    )


engine = construire_engine()


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


def construire_where_scraping(
    *,
    arrondissement: int | None = None,
    surface_min: float | None = None,
    surface_max: float | None = None,
    nombre_pieces: int | None = None,
    source: str | None = None,
) -> tuple[str, dict[str, float | int | str]]:
    """Construit la clause WHERE commune aux annonces de la table golden."""
    conditions = ["1=1"]
    params: dict[str, float | int | str] = {}
    filtres = {
        "arrondissement": (
            "localisation = :localisation",
            f"75{arrondissement:03d}" if arrondissement is not None else None,
        ),
        "surface_min": ("surface >= :surface_min", surface_min),
        "surface_max": ("surface <= :surface_max", surface_max),
        "nombre_pieces": ("nb_pieces = :nombre_pieces", nombre_pieces),
        "source": ("source = :source", source),
    }
    for nom, (condition, valeur) in filtres.items():
        if valeur is not None:
            conditions.append(condition)
            params["localisation" if nom == "arrondissement" else nom] = valeur
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

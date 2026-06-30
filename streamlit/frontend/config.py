from __future__ import annotations

"""Configuration utilisee par l'interface Streamlit en C17."""

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
# C17 : hors Docker, Streamlit parle a l'API locale sur 8000 par defaut.
# Docker Compose remplace cette valeur par http://api:8000.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_ENDPOINTS = {
    "health": "/health",
    "filtres": "/dvf/filtres",
    "stats_arrondissements": "/stats/dvf/arrondissement",
    "resume": "/stats/dvf/resume",
    "evolution": "/stats/dvf/evolution-mensuelle",
    "distribution": "/stats/dvf/distribution",
    "points": "/dvf/points",
    "csv": "/dvf/export.csv",
    "scraping_filtres": "/scraping/filtres",
    "scraping_annonces": "/scraping/annonces",
    "scraping_resume": "/stats/scraping/resume",
    "scraping_arrondissements": "/stats/scraping/arrondissement",
    "scraping_sources": "/stats/scraping/source",
    "scraping_distribution": "/stats/scraping/distribution",
    "scraping_comparaison_2025": "/stats/scraping/comparaison-dvf-2025",
    "commerces": "/commerces/paris",
    "adresse_geocodage": "/geocodage/adresse",
    # Endpoint C17 appele par le formulaire "Predire appartement".
    "prediction_prix": "/prediction/prix",
    "auth_register": "/auth/register",
    "auth_login": "/auth/login",
    "auth_me": "/auth/me",
    "auth_logout": "/auth/logout",
    "user_profile": "/users/me/profile",
    "user_password": "/users/me/password",
    "user_predictions": "/users/me/predictions",
    "user_addresses": "/users/me/addresses",
    "admin_overview": "/admin/overview",
    "admin_users": "/admin/users",
    "admin_predictions": "/admin/predictions",
    "admin_addresses": "/admin/addresses",
}
PALETTE = ["#2f8f6f", "#93c35c", "#f1e85a", "#eba148", "#c83d35"]
ZOOM_POINTS = 15
MAX_POINTS = 200000


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


def headers_api() -> dict[str, str]:
    """Construit l'en-tete X-API-Key attendu par l'API."""
    charger_env()
    api_key = os.getenv("API_KEY")
    return {"X-API-Key": api_key} if api_key else {}

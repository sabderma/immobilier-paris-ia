from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
API_BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINTS = {
    "health": "/health",
    "filtres": "/dvf/filtres",
    "stats_arrondissements": "/stats/dvf/arrondissement",
    "resume": "/stats/dvf/resume",
    "evolution": "/stats/dvf/evolution-mensuelle",
    "distribution": "/stats/dvf/distribution",
    "points": "/dvf/points",
    "csv": "/dvf/export.csv",
    "commerces": "/commerces/paris",
    "adresse_score": "/ia/noter-adresse",
    "prediction_prix": "/prediction/prix",
}
PALETTE = ["#2f8f6f", "#93c35c", "#f1e85a", "#eba148", "#c83d35"]
ZOOM_POINTS = 15
MAX_POINTS = 800


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
    charger_env()
    api_key = os.getenv("API_KEY")
    return {"X-API-Key": api_key} if api_key else {}

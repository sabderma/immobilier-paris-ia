from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL


ROOT_DIR = Path(__file__).resolve().parents[2]


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
    """Construit la connexion PostgreSQL sans mot de passe ecrit en dur."""

    charger_env()

    # DATABASE_URL est pratique en production ou en Docker.
    database_url = database_url or os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    # Sinon on reconstruit l'URL avec les variables DB_*.
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "immobilier_paris"),
    )
    return create_engine(url)

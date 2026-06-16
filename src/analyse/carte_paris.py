"""Données géographiques utilisées par la carte Streamlit de Paris."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
ARRONDISSEMENTS_CACHE = ROOT_DIR / "data/raw/arrondissements_paris.geojson"
PARIS_CENTER = [48.8566, 2.3522]


def charger_arrondissements() -> dict[str, Any]:
    """Charge les limites GeoJSON locales des arrondissements parisiens."""
    if not ARRONDISSEMENTS_CACHE.exists():
        raise FileNotFoundError(
            f"GeoJSON local introuvable : {ARRONDISSEMENTS_CACHE}"
        )

    with ARRONDISSEMENTS_CACHE.open("r", encoding="utf-8") as fichier:
        return json.load(fichier)

"""Service C17 qui execute le modele de prediction depuis l'API.

Il charge le modele sauvegarde, prepare les donnees envoyees par l'utilisateur
et retourne une estimation de prix.
"""

from __future__ import annotations

import json
from typing import Any

import joblib
import pandas as pd
from fastapi import HTTPException, status

from api.core import PREDICTION_METRICS_PATH, PREDICTION_MODEL_PATH


modele_prediction: Any | None = None


def charger_mae_prediction() -> float:
    """Lit le MAE produit lors du dernier entraînement du modèle."""
    # La MAE permet de donner une marge indicative autour du prix predit.
    if not PREDICTION_METRICS_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Métriques du modèle de prédiction introuvables.",
        )

    try:
        metriques = json.loads(PREDICTION_METRICS_PATH.read_text(encoding="utf-8"))
        mae_euros = float(metriques["mae_euros"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le MAE du modèle de prédiction est indisponible.",
        ) from exc

    if mae_euros < 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le MAE du modèle de prédiction est invalide.",
        )
    return mae_euros


def charger_modele_prediction() -> Any:
    """Charge le modele XGBoost une seule fois pour les predictions API."""
    global modele_prediction

    # On garde le modele en memoire pour eviter de relire le fichier a chaque appel.
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
    """Prepare les donnees API et lance le modele XGBoost."""
    modele = charger_modele_prediction()
    # Les noms de colonnes doivent rester identiques a ceux de l'entrainement.
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

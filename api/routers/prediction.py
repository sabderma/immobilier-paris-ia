"""Route FastAPI C17 qui expose le composant de prediction.

Cette route recoit les donnees d'un appartement, appelle le modele XGBoost et
retourne une reponse JSON au client.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from fastapi import APIRouter, Depends

from api.core import verifier_cle_api
from api.metrics import (
    MODEL_INPUT_SURFACE_M2,
    MODEL_PREDICTED_PRICE_EUROS,
    MODEL_PREDICTION_DURATION_SECONDS,
    MODEL_PREDICTION_ERRORS_TOTAL,
    MODEL_PREDICTIONS_BY_ARRONDISSEMENT,
    MODEL_PREDICTIONS_TOTAL,
)
from api.schemas import PredictionPrixRequest, PredictionPrixResponse
from api.services.auth import obtenir_utilisateur_optionnel
from api.services.prediction import charger_mae_prediction, predire_prix_xgboost
from api.services.prediction_history import enregistrer_prediction_utilisateur


router = APIRouter()


@router.post("/prediction/prix", response_model=PredictionPrixResponse)
def prediction_prix(
    payload: PredictionPrixRequest,
    _: None = Depends(verifier_cle_api),
    utilisateur: Optional[dict[str, Any]] = Depends(obtenir_utilisateur_optionnel),
) -> PredictionPrixResponse:
    """Retourne une estimation de prix avec le modele local XGBoost."""
    nom_modele = "XGBRegressor"
    arrondissement = str(payload.arrondissement)
    debut_prediction = time.perf_counter()

    try:
        # C17 : la route transforme la requete client en appel au modele IA.
        prix_estime = predire_prix_xgboost(
            surface=payload.surface,
            nombre_pieces=payload.nombre_pieces,
            arrondissement=payload.arrondissement,
        )
        mae_euros = charger_mae_prediction()
    except Exception:
        MODEL_PREDICTION_ERRORS_TOTAL.labels(model=nom_modele).inc()
        MODEL_PREDICTION_DURATION_SECONDS.labels(model=nom_modele).observe(
            time.perf_counter() - debut_prediction
        )
        raise

    # C11 : a chaque prediction, on met a jour les metriques du modele.
    MODEL_PREDICTION_DURATION_SECONDS.labels(model=nom_modele).observe(
        time.perf_counter() - debut_prediction
    )
    MODEL_PREDICTIONS_TOTAL.labels(model=nom_modele).inc()
    MODEL_PREDICTIONS_BY_ARRONDISSEMENT.labels(arrondissement=arrondissement).inc()
    MODEL_PREDICTED_PRICE_EUROS.labels(arrondissement=arrondissement).set(prix_estime)
    MODEL_INPUT_SURFACE_M2.labels(arrondissement=arrondissement).set(payload.surface)

    # Si l'utilisateur est connecte, on garde son historique de prediction.
    if utilisateur is not None:
        enregistrer_prediction_utilisateur(
            user_id=utilisateur["id"],
            surface=payload.surface,
            nombre_pieces=payload.nombre_pieces,
            arrondissement=payload.arrondissement,
            predicted_price=round(prix_estime, 2),
        )

    return PredictionPrixResponse(
        # La reponse reste structuree pour etre facile a consommer cote client.
        surface=payload.surface,
        nombre_pieces=payload.nombre_pieces,
        arrondissement=payload.arrondissement,
        prix_estime=round(prix_estime, 2),
        mae_euros=round(mae_euros, 2),
        prix_min_indicatif=round(max(0, prix_estime - mae_euros), 2),
        prix_max_indicatif=round(prix_estime + mae_euros, 2),
        modele=nom_modele,
    )

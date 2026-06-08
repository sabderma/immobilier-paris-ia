from __future__ import annotations

import json
from pathlib import Path

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from api.core import PREDICTION_METRICS_PATH


MODEL_PREDICTIONS_TOTAL = Counter(
    "model_predictions_total",
    "Nombre total de predictions realisees par le modele.",
    ["model"],
)
MODEL_PREDICTIONS_BY_ARRONDISSEMENT = Counter(
    "model_predictions_by_arrondissement_total",
    "Nombre total de predictions par arrondissement.",
    ["arrondissement"],
)
MODEL_PREDICTION_ERRORS_TOTAL = Counter(
    "model_prediction_errors_total",
    "Nombre total d'erreurs pendant les predictions du modele.",
    ["model"],
)
MODEL_PREDICTION_DURATION_SECONDS = Histogram(
    "model_prediction_duration_seconds",
    "Temps necessaire pour realiser une prediction.",
    ["model"],
)
MODEL_PREDICTED_PRICE_EUROS = Gauge(
    "model_predicted_price_euros",
    "Dernier prix estime par le modele.",
    ["arrondissement"],
)
MODEL_INPUT_SURFACE_M2 = Gauge(
    "model_input_surface_m2",
    "Derniere surface envoyee au modele.",
    ["arrondissement"],
)
MODEL_EVALUATION_MAE_EUROS = Gauge(
    "model_evaluation_mae_euros",
    "Erreur moyenne absolue du modele sur les donnees de test, en euros.",
    ["model"],
)
MODEL_EVALUATION_RMSE_EUROS = Gauge(
    "model_evaluation_rmse_euros",
    "Racine de l'erreur quadratique moyenne sur les donnees de test, en euros.",
    ["model"],
)
MODEL_EVALUATION_R2_SCORE = Gauge(
    "model_evaluation_r2_score",
    "Score R2 du modele sur les donnees de test.",
    ["model"],
)
MODEL_EVALUATION_TEST_SAMPLES = Gauge(
    "model_evaluation_test_samples",
    "Nombre de ventes utilisees pour evaluer le modele.",
    ["model"],
)


def charger_metriques_evaluation(
    metrics_path: Path = PREDICTION_METRICS_PATH,
) -> None:
    """Expose dans Prometheus les resultats produits lors de l'entrainement."""
    if not metrics_path.exists():
        return

    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    nom_modele = str(metrics.get("modele", "XGBRegressor"))
    metriques_prometheus = (
        (MODEL_EVALUATION_MAE_EUROS, "mae_euros"),
        (MODEL_EVALUATION_RMSE_EUROS, "rmse_euros"),
        (MODEL_EVALUATION_R2_SCORE, "r2_score"),
        (MODEL_EVALUATION_TEST_SAMPLES, "lignes_test"),
    )
    for gauge, cle in metriques_prometheus:
        valeur = metrics.get(cle)
        if isinstance(valeur, (int, float)):
            gauge.labels(model=nom_modele).set(valeur)


MODEL_PREDICTIONS_TOTAL.labels(model="XGBRegressor")
MODEL_PREDICTION_ERRORS_TOTAL.labels(model="XGBRegressor")
MODEL_PREDICTION_DURATION_SECONDS.labels(model="XGBRegressor")
for arrondissement in range(1, 21):
    MODEL_PREDICTIONS_BY_ARRONDISSEMENT.labels(
        arrondissement=str(arrondissement)
    )
charger_metriques_evaluation()

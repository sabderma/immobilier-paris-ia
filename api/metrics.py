"""Metriques Prometheus pour surveiller l'API et le modele IA.

Pour la C11, les metriques importantes sont surtout celles du modele :
predictions, erreurs, temps de reponse et qualite du modele.

Pour la C20, les metriques importantes sont celles de l'application complete :
requetes HTTP, latence, exceptions et etat de la base PostgreSQL.
"""

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


API_HTTP_REQUESTS_TOTAL = Counter(
    "api_http_requests_total",
    "Nombre total de requetes HTTP recues par l'API.",
    ["method", "route", "status_code"],
)
# C20 : cette metrique permet de voir combien de temps les routes mettent a repondre.
API_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "api_http_request_duration_seconds",
    "Duree des requetes HTTP traitees par l'API.",
    ["method", "route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
API_HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "api_http_requests_in_progress",
    "Nombre de requetes HTTP API en cours de traitement.",
    ["method"],
)
# C20 : si une erreur non geree arrive, elle est comptee ici.
API_EXCEPTIONS_TOTAL = Counter(
    "api_exceptions_total",
    "Nombre total d'exceptions non gerees par l'API.",
    ["method", "route", "exception_type"],
)
# C20 : cette jauge dit si PostgreSQL repond correctement.
API_DATABASE_HEALTH_STATUS = Gauge(
    "api_database_health_status",
    "Etat de la connexion PostgreSQL de l'application: 1 disponible, 0 indisponible.",
)

# C11 : ces metriques surveillent l'utilisation du modele de prediction.
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
# C11 : ces metriques gardent la qualite du modele apres l'entrainement.
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
# C11 : le dashboard suit aussi OpenAI, car c'est une fonctionnalite IA visible.
OPENAI_SUMMARY_CALLS_TOTAL = Counter(
    "openai_summary_calls_total",
    "Nombre total d'appels au service OpenAI de resume de quartier.",
    ["model", "status"],
)
OPENAI_SUMMARY_ERRORS_TOTAL = Counter(
    "openai_summary_errors_total",
    "Nombre total d'erreurs pendant les resumes OpenAI de quartier.",
    ["model"],
)
OPENAI_SUMMARY_REQUEST_DURATION_SECONDS = Histogram(
    "openai_summary_request_duration_seconds",
    "Temps necessaire pour generer un resume OpenAI de quartier.",
    ["model"],
    buckets=(0.5, 1, 2.5, 5, 10, 20, 30, 60),
)
OPENAI_SUMMARY_SERVICE_CONFIGURED = Gauge(
    "openai_summary_service_configured",
    "Etat de configuration du service OpenAI: 1 configure, 0 non configure.",
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
        # Ces valeurs viennent du fichier cree quand le modele a ete teste.
        valeur = metrics.get(cle)
        if isinstance(valeur, (int, float)):
            gauge.labels(model=nom_modele).set(valeur)


# Initialisation simple pour que Grafana voie deja les series de metriques.
MODEL_PREDICTIONS_TOTAL.labels(model="XGBRegressor")
MODEL_PREDICTION_ERRORS_TOTAL.labels(model="XGBRegressor")
MODEL_PREDICTION_DURATION_SECONDS.labels(model="XGBRegressor")
OPENAI_SUMMARY_CALLS_TOTAL.labels(model="gpt-5.4-mini", status="success")
OPENAI_SUMMARY_CALLS_TOTAL.labels(model="gpt-5.4-mini", status="error")
OPENAI_SUMMARY_ERRORS_TOTAL.labels(model="gpt-5.4-mini")
OPENAI_SUMMARY_REQUEST_DURATION_SECONDS.labels(model="gpt-5.4-mini")
OPENAI_SUMMARY_SERVICE_CONFIGURED.labels(model="gpt-5.4-mini").set(0)
for arrondissement in range(1, 21):
    MODEL_PREDICTIONS_BY_ARRONDISSEMENT.labels(
        arrondissement=str(arrondissement)
    )
API_DATABASE_HEALTH_STATUS.set(0)
charger_metriques_evaluation()

from __future__ import annotations

"""Point d'entree de l'API REST du projet.

Ce fichier cree l'application FastAPI, ajoute les middlewares, branche les routes
et garde les logs/metriques des appels HTTP.
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.logging_config import configurer_journalisation
from api.metrics import (
    API_EXCEPTIONS_TOTAL,
    API_HTTP_REQUEST_DURATION_SECONDS,
    API_HTTP_REQUESTS_IN_PROGRESS,
    API_HTTP_REQUESTS_TOTAL,
)
from api.routers import admin, auth, dvf, location, prediction, scraping, stats, system, users
from api.services.auth import initialiser_super_admin_depuis_env


configurer_journalisation()
logger = logging.getLogger("immobilier_paris.api")

# Objet principal FastAPI. C'est lui qui expose aussi Swagger sur /docs.
app = FastAPI(
    title="API Immobilier Paris",
    description="API REST pour les données immobilières de Paris",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    # C17 : l'API accepte l'interface Streamlit locale comme client.
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def initialiser_comptes_systeme() -> None:
    """Prepare les comptes systeme quand l'API demarre."""
    try:
        super_admin_initialise = initialiser_super_admin_depuis_env()
    except Exception:
        logger.exception(
            "super_admin_initialization_failed",
            extra={"event": "super_admin_initialization_failed"},
        )
        return

    if super_admin_initialise:
        logger.info(
            "super_admin_initialized",
            extra={"event": "super_admin_initialized"},
        )


def _route_label(request: Request) -> str:
    """Recupere le nom stable de la route pour les logs et les metriques."""
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return route_path
    return request.url.path


@app.middleware("http")
async def monitorer_requetes_http(request: Request, call_next):
    """Mesure chaque requete HTTP pour savoir si l'API repond bien."""
    # C20 : on ne compte pas /metrics, sinon Prometheus fausse les statistiques.
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    debut = time.perf_counter()
    # C20 : on sait combien de requetes sont en train d'etre traitees.
    API_HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

    try:
        response = await call_next(request)
    except Exception as exc:
        duree = time.perf_counter() - debut
        route = _route_label(request)
        # C20 : une exception est comptee comme erreur 500 pour le monitoring.
        API_HTTP_REQUESTS_TOTAL.labels(
            method=method,
            route=route,
            status_code="500",
        ).inc()
        API_HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            route=route,
        ).observe(duree)
        API_EXCEPTIONS_TOTAL.labels(
            method=method,
            route=route,
            exception_type=type(exc).__name__,
        ).inc()
        API_HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()
        # C20 : le log garde le contexte technique sans stocker le corps de la requete.
        logger.exception(
            "api_request_failed",
            extra={
                "event": "api_request_failed",
                "http_method": method,
                "http_route": route,
                "http_status_code": 500,
                "duration_ms": round(duree * 1000, 2),
                "client_ip": request.client.host if request.client else None,
            },
        )
        raise

    duree = time.perf_counter() - debut
    route = _route_label(request)
    status_code = str(response.status_code)
    # C20 : chaque requete normale augmente les compteurs Prometheus.
    API_HTTP_REQUESTS_TOTAL.labels(
        method=method,
        route=route,
        status_code=status_code,
    ).inc()
    API_HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        route=route,
    ).observe(duree)
    API_HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()
    # C20 : ce log aide a comprendre les routes lentes ou en erreur.
    logger.info(
        "api_request_completed",
        extra={
            "event": "api_request_completed",
            "http_method": method,
            "http_route": route,
            "http_status_code": response.status_code,
            "duration_ms": round(duree * 1000, 2),
            "client_ip": request.client.host if request.client else None,
        },
    )
    return response


# C17 : chaque routeur correspond a une partie developpee de l'application.
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(prediction.router)
app.include_router(location.router)
app.include_router(dvf.router)
app.include_router(scraping.router)
app.include_router(stats.router)

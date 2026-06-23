from __future__ import annotations

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


configurer_journalisation()
logger = logging.getLogger("immobilier_paris.api")

app = FastAPI(
    title="API Immobilier Paris",
    description="API REST pour les données immobilières de Paris",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return route_path
    return request.url.path


@app.middleware("http")
async def monitorer_requetes_http(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    debut = time.perf_counter()
    API_HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

    try:
        response = await call_next(request)
    except Exception as exc:
        duree = time.perf_counter() - debut
        route = _route_label(request)
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


app.include_router(system.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(prediction.router)
app.include_router(location.router)
app.include_router(dvf.router)
app.include_router(scraping.router)
app.include_router(stats.router)

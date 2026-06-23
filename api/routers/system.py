from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import text

from api.core import engine
from api.metrics import API_DATABASE_HEALTH_STATUS, CONTENT_TYPE_LATEST, generate_latest


router = APIRouter()


@router.get("/")
def accueil() -> dict[str, str]:
    return {
        "message": "API Immobilier Paris fonctionne",
        "documentation": "http://127.0.0.1:8000/docs",
    }


def actualiser_sante_base() -> Exception | None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        API_DATABASE_HEALTH_STATUS.set(1)
        return None
    except Exception as exc:
        API_DATABASE_HEALTH_STATUS.set(0)
        return exc


@router.get("/health")
def health_check() -> dict[str, str]:
    erreur = actualiser_sante_base()
    if erreur is not None:
        exc = erreur
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "ok", "database": "connectée"}


@router.get("/metrics")
def metrics() -> Response:
    actualiser_sante_base()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import text

from api.core import engine
from api.metrics import CONTENT_TYPE_LATEST, generate_latest


router = APIRouter()


@router.get("/")
def accueil() -> dict[str, str]:
    return {
        "message": "API Immobilier Paris fonctionne",
        "documentation": "http://127.0.0.1:8000/docs",
    }


@router.get("/health")
def health_check() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connectée"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

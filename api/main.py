from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import admin, auth, dvf, location, prediction, scraping, stats, system, users


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

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(prediction.router)
app.include_router(location.router)
app.include_router(dvf.router)
app.include_router(scraping.router)
app.include_router(stats.router)

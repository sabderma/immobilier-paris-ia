from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PredictionPrixRequest(BaseModel):
    surface: float = Field(gt=0, description="Surface du bien en m2")
    nombre_pieces: int = Field(gt=0, description="Nombre de pieces principales")
    arrondissement: int = Field(ge=1, le=20, description="Arrondissement parisien")


class PredictionPrixResponse(BaseModel):
    surface: float
    nombre_pieces: int
    arrondissement: int
    prix_estime: float
    mae_euros: float
    prix_min_indicatif: float
    prix_max_indicatif: float
    modele: str


class PredictionHistoriqueResponse(BaseModel):
    id: int
    user_id: int
    surface: float
    nb_pieces: int
    arrondissement: int
    predicted_price: float
    created_at: datetime


class AdresseHistoriqueResponse(BaseModel):
    id: int
    user_id: int
    address: str
    latitude: float
    longitude: float
    created_at: datetime


class AdresseGeocodageRequest(BaseModel):
    adresse: str = Field(min_length=3, max_length=200, description="Adresse exacte")

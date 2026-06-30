"""Schemas Pydantic utiles aux routes API developpees en C17.

Ils definissent ce que le client doit envoyer et ce que l'API retourne.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


SURFACE_MIN_M2 = 9
SURFACE_MAX_M2 = 300
NOMBRE_PIECES_MIN = 1
NOMBRE_PIECES_MAX = 12


class PredictionPrixRequest(BaseModel):
    """Donnees autorisees en entree pour appeler le modele."""

    surface: float = Field(
        ge=SURFACE_MIN_M2,
        le=SURFACE_MAX_M2,
        description="Surface du bien en m2",
    )
    nombre_pieces: int = Field(
        ge=NOMBRE_PIECES_MIN,
        le=NOMBRE_PIECES_MAX,
        description="Nombre de pieces principales",
    )
    arrondissement: int = Field(ge=1, le=20, description="Arrondissement parisien")


class PredictionPrixResponse(BaseModel):
    """Reponse JSON renvoyee apres l'execution du modele."""

    surface: float
    nombre_pieces: int
    arrondissement: int
    prix_estime: float
    mae_euros: float
    prix_min_indicatif: float
    prix_max_indicatif: float
    modele: str


class PredictionHistoriqueResponse(BaseModel):
    """Format renvoye pour une prediction sauvegardee."""

    id: int
    user_id: int
    surface: float
    nb_pieces: int
    arrondissement: int
    predicted_price: float
    created_at: datetime


class AdresseHistoriqueResponse(BaseModel):
    """Format renvoye pour une adresse sauvegardee."""

    id: int
    user_id: int
    address: str
    latitude: float
    longitude: float
    created_at: datetime


class AdresseGeocodageRequest(BaseModel):
    """Adresse saisie par l'utilisateur depuis l'interface."""

    adresse: str = Field(min_length=3, max_length=200, description="Adresse exacte")

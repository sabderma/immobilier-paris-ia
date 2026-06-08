from __future__ import annotations

from typing import Any, Optional

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


class AdresseScoreRequest(BaseModel):
    adresse: str = Field(min_length=3, max_length=200, description="Adresse exacte")
    arrondissement: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Arrondissement parisien optionnel",
    )


GEMINI_CATEGORIE_LIEUX_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "nombre_trouve": {"type": "integer"},
        "elements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string"},
                    "type": {"type": "string"},
                    "lignes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "distance_estimee": {"type": "string"},
                    "temps_a_pied": {"type": "string"},
                    "impact": {"type": "string"},
                    "commentaire": {"type": "string"},
                },
            },
        },
    },
}


GEMINI_ADRESSE_SCORE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "adresse_analysee": {"type": "string"},
        "score_global": {"type": "integer"},
        "niveau": {"type": "string"},
        "resume": {"type": "string"},
        "details": {
            "type": "object",
            "properties": {
                "transports": GEMINI_CATEGORIE_LIEUX_SCHEMA,
                "commerces": GEMINI_CATEGORIE_LIEUX_SCHEMA,
                "ecoles": GEMINI_CATEGORIE_LIEUX_SCHEMA,
                "espaces_verts": GEMINI_CATEGORIE_LIEUX_SCHEMA,
                "sante": GEMINI_CATEGORIE_LIEUX_SCHEMA,
                "tourisme_frequentation": GEMINI_CATEGORIE_LIEUX_SCHEMA,
                "tranquillite": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer"},
                        "avis": {"type": "string"},
                        "risques": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "attractivite_immobiliere": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer"},
                        "avis": {"type": "string"},
                    },
                },
            },
        },
        "points_forts": {"type": "array", "items": {"type": "string"}},
        "points_faibles": {"type": "array", "items": {"type": "string"}},
        "conclusion_acheteur": {"type": "string"},
    },
}

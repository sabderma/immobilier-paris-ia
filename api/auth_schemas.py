from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def valider_email(cls, valeur: str) -> str:
        email = valeur.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Adresse email invalide")
        return email

    @field_validator("first_name", "last_name")
    @classmethod
    def nettoyer_nom(cls, valeur: Optional[str]) -> Optional[str]:
        if valeur is None:
            return None
        return valeur.strip() or None


class UtilisateurResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    created_at: datetime


class ConnexionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def valider_email(cls, valeur: str) -> str:
        email = valeur.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Adresse email invalide")
        return email


class ConnexionResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    utilisateur: UtilisateurResponse


class MessageResponse(BaseModel):
    message: str


class ProfilUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("first_name", "last_name")
    @classmethod
    def nettoyer_nom(cls, valeur: Optional[str]) -> Optional[str]:
        if valeur is None:
            return None
        return valeur.strip() or None


class MotDePasseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from api.auth_schemas import (
    ConnexionRequest,
    ConnexionResponse,
    InscriptionRequest,
    MessageResponse,
    UtilisateurResponse,
)
from api.services.auth import (
    connecter_utilisateur,
    creer_utilisateur,
    obtenir_utilisateur_courant,
)


router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post(
    "/register",
    response_model=UtilisateurResponse,
    status_code=status.HTTP_201_CREATED,
)
def inscription(payload: InscriptionRequest) -> UtilisateurResponse:
    utilisateur = creer_utilisateur(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UtilisateurResponse.model_validate(utilisateur)


@router.post("/login", response_model=ConnexionResponse)
def connexion(payload: ConnexionRequest) -> ConnexionResponse:
    resultat = connecter_utilisateur(email=payload.email, password=payload.password)
    return ConnexionResponse.model_validate(resultat)


@router.get("/me", response_model=UtilisateurResponse)
def profil_connecte(
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> UtilisateurResponse:
    return UtilisateurResponse.model_validate(utilisateur)


@router.post("/logout", response_model=MessageResponse)
def deconnexion(
    _: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> MessageResponse:
    return MessageResponse(message="Déconnexion réussie.")

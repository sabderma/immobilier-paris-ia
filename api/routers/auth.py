from __future__ import annotations

"""Routes C17 pour inscription, connexion et deconnexion."""

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
    """Cree un utilisateur depuis le formulaire Streamlit."""
    utilisateur = creer_utilisateur(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UtilisateurResponse.model_validate(utilisateur)


@router.post("/login", response_model=ConnexionResponse)
def connexion(payload: ConnexionRequest) -> ConnexionResponse:
    """Verifie les identifiants et retourne un token JWT."""
    resultat = connecter_utilisateur(email=payload.email, password=payload.password)
    return ConnexionResponse.model_validate(resultat)


@router.get("/me", response_model=UtilisateurResponse)
def profil_connecte(
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> UtilisateurResponse:
    """Retourne le profil de l'utilisateur connecte."""
    return UtilisateurResponse.model_validate(utilisateur)


@router.post("/logout", response_model=MessageResponse)
def deconnexion(
    _: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> MessageResponse:
    """Confirme la deconnexion cote API."""
    return MessageResponse(message="Déconnexion réussie.")

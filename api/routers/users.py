from __future__ import annotations

"""Routes C17 pour les actions du compte utilisateur connecte."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.auth_schemas import (
    MessageResponse,
    MotDePasseUpdateRequest,
    ProfilUpdateRequest,
    UtilisateurResponse,
)
from api.schemas import AdresseHistoriqueResponse, PredictionHistoriqueResponse
from api.services.auth import (
    changer_mot_de_passe_utilisateur,
    mettre_a_jour_profil_utilisateur,
    obtenir_utilisateur_courant,
)
from api.services.address_history import (
    lister_adresses_utilisateur,
    supprimer_adresse_utilisateur,
)
from api.services.prediction_history import (
    lister_predictions_utilisateur,
    supprimer_prediction_utilisateur,
)


router = APIRouter(prefix="/users/me", tags=["Utilisateur"])


@router.patch("/profile", response_model=UtilisateurResponse)
def modifier_profil(
    payload: ProfilUpdateRequest,
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> UtilisateurResponse:
    """Modifie le prenom ou le nom de l'utilisateur connecte."""
    donnees = payload.model_dump(exclude_unset=True)
    if not donnees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune information à modifier.",
        )

    utilisateur_modifie = mettre_a_jour_profil_utilisateur(
        user_id=utilisateur["id"],
        first_name=donnees.get("first_name", utilisateur["first_name"]),
        last_name=donnees.get("last_name", utilisateur["last_name"]),
    )
    return UtilisateurResponse.model_validate(utilisateur_modifie)


@router.patch("/password", response_model=MessageResponse)
def modifier_mot_de_passe(
    payload: MotDePasseUpdateRequest,
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> MessageResponse:
    """Change le mot de passe de l'utilisateur connecte."""
    changer_mot_de_passe_utilisateur(
        user_id=utilisateur["id"],
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Mot de passe modifié avec succès.")


@router.get("/predictions", response_model=list[PredictionHistoriqueResponse])
def historique_predictions(
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> list[PredictionHistoriqueResponse]:
    """Liste les predictions sauvegardees de l'utilisateur."""
    predictions = lister_predictions_utilisateur(utilisateur["id"])
    return [
        PredictionHistoriqueResponse.model_validate(prediction)
        for prediction in predictions
    ]


@router.delete("/predictions/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_prediction(
    prediction_id: int,
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> Response:
    """Supprime une prediction seulement si elle appartient a l'utilisateur."""
    prediction_supprimee = supprimer_prediction_utilisateur(
        user_id=utilisateur["id"],
        prediction_id=prediction_id,
    )
    if not prediction_supprimee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prédiction introuvable.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/addresses", response_model=list[AdresseHistoriqueResponse])
def historique_adresses(
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> list[AdresseHistoriqueResponse]:
    """Liste les adresses sauvegardees de l'utilisateur."""
    adresses = lister_adresses_utilisateur(utilisateur["id"])
    return [
        AdresseHistoriqueResponse.model_validate(adresse)
        for adresse in adresses
    ]


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_adresse(
    address_id: int,
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> Response:
    """Supprime une adresse seulement si elle appartient a l'utilisateur."""
    adresse_supprimee = supprimer_adresse_utilisateur(
        user_id=utilisateur["id"],
        address_id=address_id,
    )
    if not adresse_supprimee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adresse introuvable.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

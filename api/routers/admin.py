from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from api.core import engine
from api.services.auth import obtenir_admin_courant


router = APIRouter(prefix="/admin", tags=["Admin"])
ROLE_SUPER_ADMIN = "super_admin"


class AdminOverviewResponse(BaseModel):
    total_users: int
    total_admins: int
    total_regular_users: int
    total_active_users: int
    total_predictions: int
    total_addresses: int


class AdminUserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class AdminRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern="^(user|admin)$")


class AdminPredictionResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    first_name: Optional[str]
    last_name: Optional[str]
    surface: float
    nb_pieces: int
    arrondissement: int
    predicted_price: float
    created_at: datetime


class AdminAddressResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    first_name: Optional[str]
    last_name: Optional[str]
    address: str
    latitude: float
    longitude: float
    created_at: datetime


@router.get("/overview", response_model=AdminOverviewResponse)
def overview_admin(
    _: dict[str, Any] = Depends(obtenir_admin_courant),
) -> AdminOverviewResponse:
    with engine.connect() as connexion:
        ligne = connexion.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM users) AS total_users,
                    (SELECT COUNT(*) FROM users WHERE role IN ('admin', 'super_admin')) AS total_admins,
                    (SELECT COUNT(*) FROM users WHERE role = 'user') AS total_regular_users,
                    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) AS total_active_users,
                    (SELECT COUNT(*) FROM predictions) AS total_predictions,
                    (SELECT COUNT(*) FROM exact_address_history) AS total_addresses;
                """
            )
        ).mappings().one()

    return AdminOverviewResponse.model_validate(dict(ligne))


@router.get("/users", response_model=list[AdminUserResponse])
def lister_utilisateurs_admin(
    _: dict[str, Any] = Depends(obtenir_admin_courant),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AdminUserResponse]:
    with engine.connect() as connexion:
        lignes = connexion.execute(
            text(
                """
                SELECT id, email, first_name, last_name, role, is_active, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        ).mappings().all()

    return [AdminUserResponse.model_validate(dict(ligne)) for ligne in lignes]


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def modifier_role_utilisateur_admin(
    user_id: int,
    payload: AdminRoleUpdateRequest,
    admin: dict[str, Any] = Depends(obtenir_admin_courant),
) -> AdminUserResponse:
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu ne peux pas modifier ton propre rôle admin.",
        )

    with engine.begin() as connexion:
        utilisateur_cible = connexion.execute(
            text(
                """
                SELECT id, role
                FROM users
                WHERE id = :user_id
                LIMIT 1;
                """
            ),
            {"user_id": user_id},
        ).mappings().one_or_none()

        if utilisateur_cible is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        if utilisateur_cible["role"] == ROLE_SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Le super admin ne peut pas être modifié.",
            )

        utilisateur = connexion.execute(
            text(
                """
                UPDATE users
                SET role = :role, updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
                RETURNING id, email, first_name, last_name, role, is_active, created_at;
                """
            ),
            {"user_id": user_id, "role": payload.role},
        ).mappings().one_or_none()

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    return AdminUserResponse.model_validate(dict(utilisateur))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_utilisateur_admin(
    user_id: int,
    admin: dict[str, Any] = Depends(obtenir_admin_courant),
) -> Response:
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu ne peux pas supprimer ton propre compte admin.",
        )

    with engine.begin() as connexion:
        utilisateur_cible = connexion.execute(
            text(
                """
                SELECT id, role
                FROM users
                WHERE id = :user_id
                LIMIT 1;
                """
            ),
            {"user_id": user_id},
        ).mappings().one_or_none()

        if utilisateur_cible is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        if utilisateur_cible["role"] == ROLE_SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Le super admin ne peut pas être supprimé.",
            )

        resultat = connexion.execute(
            text(
                """
                DELETE FROM users
                WHERE id = :user_id;
                """
            ),
            {"user_id": user_id},
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/predictions", response_model=list[AdminPredictionResponse])
def lister_predictions_admin(
    _: dict[str, Any] = Depends(obtenir_admin_courant),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AdminPredictionResponse]:
    with engine.connect() as connexion:
        lignes = connexion.execute(
            text(
                """
                SELECT
                    p.id,
                    p.user_id,
                    u.email AS user_email,
                    u.first_name,
                    u.last_name,
                    p.surface,
                    p.nb_pieces,
                    p.arrondissement,
                    p.predicted_price,
                    p.created_at
                FROM predictions p
                JOIN users u ON u.id = p.user_id
                ORDER BY p.created_at DESC
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        ).mappings().all()

    return [AdminPredictionResponse.model_validate(dict(ligne)) for ligne in lignes]


@router.get("/addresses", response_model=list[AdminAddressResponse])
def lister_adresses_admin(
    _: dict[str, Any] = Depends(obtenir_admin_courant),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AdminAddressResponse]:
    with engine.connect() as connexion:
        lignes = connexion.execute(
            text(
                """
                SELECT
                    a.id,
                    a.user_id,
                    u.email AS user_email,
                    u.first_name,
                    u.last_name,
                    a.address,
                    a.latitude,
                    a.longitude,
                    a.created_at
                FROM exact_address_history a
                JOIN users u ON u.id = a.user_id
                ORDER BY a.created_at DESC
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        ).mappings().all()

    return [AdminAddressResponse.model_validate(dict(ligne)) for ligne in lignes]

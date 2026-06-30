from __future__ import annotations

"""Service C17 pour sauvegarder l'historique des adresses utilisateur."""

from typing import Any

from sqlalchemy import text

from api.core import engine


def enregistrer_adresse_utilisateur(
    *,
    user_id: int,
    address: str,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Enregistre une adresse exacte validée par un utilisateur connecté."""
    # C17 : on garde seulement les adresses validees par le geocodage.
    with engine.begin() as connexion:
        adresse = connexion.execute(
            text(
                """
                INSERT INTO exact_address_history (
                    user_id,
                    address,
                    latitude,
                    longitude
                )
                VALUES (
                    :user_id,
                    :address,
                    :latitude,
                    :longitude
                )
                RETURNING
                    id,
                    user_id,
                    address,
                    latitude::FLOAT AS latitude,
                    longitude::FLOAT AS longitude,
                    created_at;
                """
            ),
            {
                "user_id": user_id,
                "address": address,
                "latitude": latitude,
                "longitude": longitude,
            },
        ).mappings().one()

    return dict(adresse)


def lister_adresses_utilisateur(user_id: int) -> list[dict[str, Any]]:
    """Liste les adresses exactes de l'utilisateur connecté."""
    # C17 : l'utilisateur voit uniquement ses propres adresses.
    with engine.connect() as connexion:
        adresses = connexion.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    address,
                    latitude::FLOAT AS latitude,
                    longitude::FLOAT AS longitude,
                    created_at
                FROM exact_address_history
                WHERE user_id = :user_id
                ORDER BY created_at DESC, id DESC;
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

    return [dict(adresse) for adresse in adresses]


def supprimer_adresse_utilisateur(*, user_id: int, address_id: int) -> bool:
    """Supprime une adresse seulement si elle appartient à l'utilisateur."""
    # C17 : la suppression est limitee a l'adresse du compte connecte.
    with engine.begin() as connexion:
        resultat = connexion.execute(
            text(
                """
                DELETE FROM exact_address_history
                WHERE id = :address_id
                  AND user_id = :user_id;
                """
            ),
            {"address_id": address_id, "user_id": user_id},
        )

    return resultat.rowcount == 1

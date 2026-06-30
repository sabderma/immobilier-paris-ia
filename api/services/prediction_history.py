from __future__ import annotations

"""Service C17 pour sauvegarder l'historique des predictions utilisateur."""

from typing import Any

from sqlalchemy import text

from api.core import engine


def enregistrer_prediction_utilisateur(
    *,
    user_id: int,
    surface: float,
    nombre_pieces: int,
    arrondissement: int,
    predicted_price: float,
) -> dict[str, Any]:
    """Enregistre une prédiction réalisée par un utilisateur connecté."""
    # C17 : l'historique permet d'afficher les anciennes predictions dans Streamlit.
    with engine.begin() as connexion:
        prediction = connexion.execute(
            text(
                """
                INSERT INTO predictions (
                    user_id,
                    surface,
                    nb_pieces,
                    arrondissement,
                    predicted_price
                )
                VALUES (
                    :user_id,
                    :surface,
                    :nb_pieces,
                    :arrondissement,
                    :predicted_price
                )
                RETURNING
                    id,
                    user_id,
                    surface::FLOAT AS surface,
                    nb_pieces,
                    arrondissement,
                    predicted_price::FLOAT AS predicted_price,
                    created_at;
                """
            ),
            {
                "user_id": user_id,
                "surface": surface,
                "nb_pieces": nombre_pieces,
                "arrondissement": arrondissement,
                "predicted_price": predicted_price,
            },
        ).mappings().one()

    return dict(prediction)


def lister_predictions_utilisateur(user_id: int) -> list[dict[str, Any]]:
    """Liste les prédictions de l'utilisateur connecté, de la plus récente à l'ancienne."""
    # C17 : on filtre toujours par user_id pour ne pas melanger les utilisateurs.
    with engine.connect() as connexion:
        predictions = connexion.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    surface::FLOAT AS surface,
                    nb_pieces,
                    arrondissement,
                    predicted_price::FLOAT AS predicted_price,
                    created_at
                FROM predictions
                WHERE user_id = :user_id
                ORDER BY created_at DESC, id DESC;
                """
            ),
            {"user_id": user_id},
        ).mappings().all()

    return [dict(prediction) for prediction in predictions]


def supprimer_prediction_utilisateur(*, user_id: int, prediction_id: int) -> bool:
    """Supprime une prédiction seulement si elle appartient à l'utilisateur."""
    # C17 : la condition user_id evite de supprimer la prediction d'un autre compte.
    with engine.begin() as connexion:
        resultat = connexion.execute(
            text(
                """
                DELETE FROM predictions
                WHERE id = :prediction_id
                  AND user_id = :user_id;
                """
            ),
            {"prediction_id": prediction_id, "user_id": user_id},
        )

    return resultat.rowcount == 1

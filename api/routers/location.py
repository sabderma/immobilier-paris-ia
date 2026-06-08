from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from api.core import verifier_cle_api
from api.schemas import AdresseScoreRequest
from api.services.address import (
    adresse_hors_paris,
    arrondissement_dans_adresse,
    generer_score_adresse_gemini,
    normaliser_adresse_paris,
)
from api.services.commerces import charger_commerces_paris


router = APIRouter()


@router.post("/ia/noter-adresse")
def noter_adresse(
    payload: AdresseScoreRequest,
    _: None = Depends(verifier_cle_api),
) -> dict[str, Any]:
    if adresse_hors_paris(payload.adresse):
        return {
            "erreur": "Adresse non valide",
            "message": "Il faut saisir une adresse située à Paris.",
        }

    arrondissement_detecte = arrondissement_dans_adresse(payload.adresse)
    if (
        arrondissement_detecte is not None
        and payload.arrondissement is not None
        and arrondissement_detecte != payload.arrondissement
    ):
        return {
            "erreur": "Arrondissement incohérent",
            "message": (
                f"L'adresse indique Paris {arrondissement_detecte}, "
                f"mais l'arrondissement sélectionné est Paris {payload.arrondissement}."
            ),
        }

    arrondissement = arrondissement_detecte or payload.arrondissement
    if arrondissement is None:
        return {
            "erreur": "Adresse incomplète",
            "message": "Il faut saisir une adresse complète avec Paris et l'arrondissement.",
        }

    adresse_complete = normaliser_adresse_paris(payload.adresse, arrondissement)
    return generer_score_adresse_gemini(adresse_complete, arrondissement)


@router.get("/commerces/paris")
def commerces_paris(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = Query(None, ge=1, le=20),
) -> dict:
    commerces = list(charger_commerces_paris())
    if arrondissement is not None:
        commerces = [
            commerce
            for commerce in commerces
            if commerce["arrondissement"] == arrondissement
        ]

    return {
        "source": "Open data Ile-de-France - Base permanente des equipements 2012",
        "nombre_resultats": len(commerces),
        "data": commerces,
    }

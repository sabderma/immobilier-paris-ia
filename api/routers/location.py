from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from api.core import verifier_cle_api
from api.schemas import AdresseGeocodageRequest
from api.services.auth import obtenir_utilisateur_optionnel
from api.services.address import geocoder_adresse_ign
from api.services.address_history import enregistrer_adresse_utilisateur
from api.services.commerces import charger_commerces_paris
from api.services.location_summary import generer_resume_lieu
from api.services.proximity import analyser_proximite


router = APIRouter()


@router.post("/geocodage/adresse")
def geocoder_adresse(
    payload: AdresseGeocodageRequest,
    _: None = Depends(verifier_cle_api),
    utilisateur: Optional[dict[str, Any]] = Depends(obtenir_utilisateur_optionnel),
) -> dict[str, Any]:
    resultat = geocoder_adresse_ign(payload.adresse)
    if not resultat.get("erreur"):
        if utilisateur is not None:
            enregistrer_adresse_utilisateur(
                user_id=utilisateur["id"],
                address=resultat["adresse_normalisee"],
                latitude=resultat["latitude"],
                longitude=resultat["longitude"],
            )
        proximite = analyser_proximite(
            resultat["latitude"],
            resultat["longitude"],
        )
        resultat["proximite"] = proximite
        resultat["resume_ia"] = generer_resume_lieu(
            resultat["adresse_normalisee"],
            proximite,
        )
    return resultat


@router.get("/commerces/paris")
def commerces_paris(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = Query(None, ge=1, le=20),
) -> dict:
    commerces = list(charger_commerces_paris())
    source_etat = "disponible" if commerces else "indisponible"
    if arrondissement is not None:
        commerces = [
            commerce
            for commerce in commerces
            if commerce["arrondissement"] == arrondissement
        ]

    return {
        "source": "Open data Ile-de-France - Base permanente des equipements 2012",
        "source_etat": source_etat,
        "nombre_resultats": len(commerces),
        "data": commerces,
    }

from __future__ import annotations

"""Service de geocodage utilise par les routes API en C17.

Il transforme une adresse saisie en adresse normalisee avec latitude et longitude.
"""

from typing import Any

import requests
from fastapi import HTTPException, status


GEOCODAGE_IGN_API_URL = "https://data.geopf.fr/geocodage/search"
TIMEOUT_GEOCODAGE_SECONDES = 15


def arrondissement_depuis_code_postal(code_postal: str) -> int | None:
    """Recupere l'arrondissement depuis un code postal parisien."""
    if len(code_postal) != 5 or not code_postal.startswith("750"):
        return None

    try:
        arrondissement = int(code_postal[-2:])
    except ValueError:
        return None

    return arrondissement if 1 <= arrondissement <= 20 else None


def est_adresse_exacte_paris(feature: dict[str, Any]) -> bool:
    """Verifie que le resultat est bien une adresse exacte dans Paris."""
    proprietes = feature.get("properties", {})
    code_postal = str(proprietes.get("postcode") or "")
    return (
        proprietes.get("type") == "housenumber"
        and arrondissement_depuis_code_postal(code_postal) is not None
        and proprietes.get("city") == "Paris"
    )


def normaliser_resultat_ign(
    adresse_saisie: str,
    feature: dict[str, Any],
) -> dict[str, Any]:
    """Met la reponse geocodage dans un format simple pour l'API."""
    proprietes = feature["properties"]
    longitude, latitude = feature["geometry"]["coordinates"]
    code_postal = str(proprietes["postcode"])

    return {
        "source": "Géoplateforme IGN - Base Adresse Nationale",
        "adresse_saisie": adresse_saisie,
        "adresse_normalisee": proprietes["label"],
        "identifiant_ban": proprietes.get("id"),
        "numero": proprietes.get("housenumber"),
        "voie": proprietes.get("street"),
        "code_postal": code_postal,
        "ville": proprietes.get("city"),
        "arrondissement": arrondissement_depuis_code_postal(code_postal),
        "longitude": float(longitude),
        "latitude": float(latitude),
        "score_correspondance": round(float(proprietes.get("score", 0)), 4),
        "type_resultat": proprietes.get("type"),
    }


def geocoder_adresse_ign(adresse: str) -> dict[str, Any]:
    """Appelle le service de geocodage et gere les cas d'erreur."""
    # C17 : on nettoie les espaces pour envoyer une adresse plus propre a IGN.
    adresse_saisie = " ".join(adresse.strip().split())

    try:
        response = requests.get(
            GEOCODAGE_IGN_API_URL,
            params={
                "q": adresse_saisie,
                "limit": 5,
                "index": "address",
            },
            timeout=TIMEOUT_GEOCODAGE_SECONDES,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de géocodage IGN est temporairement indisponible.",
        ) from exc

    features = payload.get("features", [])
    meilleur_resultat = features[0] if features else None
    if meilleur_resultat is not None and est_adresse_exacte_paris(meilleur_resultat):
        # C17 : seule une adresse exacte a Paris est acceptee.
        return normaliser_resultat_ign(adresse_saisie, meilleur_resultat)

    if meilleur_resultat is not None and (
        meilleur_resultat.get("properties", {}).get("city") == "Paris"
    ):
        return {
            "erreur": "Adresse exacte introuvable",
            "message": (
                "Indiquez une adresse parisienne complète avec un numéro et un nom de voie."
            ),
        }

    if meilleur_resultat is not None:
        return {
            "erreur": "Adresse non valide",
            "message": "Il faut saisir une adresse exacte située à Paris.",
        }

    return {
        "erreur": "Adresse introuvable",
        "message": "Aucune adresse correspondante n’a été trouvée.",
    }

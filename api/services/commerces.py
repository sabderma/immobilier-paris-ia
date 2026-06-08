from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd
import requests
from fastapi import HTTPException, status

from api.core import CHAMPS_COMMERCES, COMMERCES_PARIS_API_URL


def valeur_entier(donnees: dict[str, Any], champ: str) -> int:
    valeur = donnees.get(champ)
    if valeur is None or pd.isna(valeur):
        return 0
    return int(valeur)


def nom_arrondissement(donnees: dict[str, Any]) -> str:
    libelle = donnees.get("libelle_de_commune")
    if isinstance(libelle, list) and libelle:
        return str(libelle[0])
    if libelle:
        return str(libelle)
    numero = int(donnees.get("departement_commune", 75100)) - 75100
    suffixe = "er" if numero == 1 else "e"
    return f"Paris {numero}{suffixe} Arrondissement"


def normaliser_commerce_arrondissement(donnees: dict[str, Any]) -> dict[str, Any]:
    departement_commune = int(donnees["departement_commune"])
    population = valeur_entier(donnees, "population_2010")
    total_commerces = sum(valeur_entier(donnees, champ) for champ in CHAMPS_COMMERCES)
    commerces_pour_10000_habitants = (
        round(total_commerces / population * 10000, 1) if population else None
    )
    geo_point = donnees.get("geo_point_2d") or {}

    return {
        "arrondissement": departement_commune - 75100,
        "departement_commune": departement_commune,
        "nom_arrondissement": nom_arrondissement(donnees),
        "population_2010": population,
        "total_commerces": total_commerces,
        "commerces_pour_10000_habitants": commerces_pour_10000_habitants,
        "grandes_surfaces": sum(
            valeur_entier(donnees, champ)
            for champ in [
                "hypermarche",
                "supermarche",
                "grande_surface_de_bricolage",
            ]
        ),
        "commerces_alimentaires": sum(
            valeur_entier(donnees, champ)
            for champ in [
                "superette",
                "epicerie",
                "boulangerie",
                "boucherie_charcuterie",
                "produits_surgeles",
                "poissonnerie",
            ]
        ),
        "commerces_specialises": sum(
            valeur_entier(donnees, champ)
            for champ in [
                "librairie_papeterie_journaux",
                "magasin_de_vetements",
                "magasin_d_equipements_du_foyer",
                "magasin_de_chaussures",
                "magasin_d_electromenager_et_de_mat_audio_video",
                "magasin_de_meubles",
                "magasin_d_articles_de_sports_et_de_loisirs",
                "magasin_de_revetements_murs_et_sols",
                "droguerie_quincaillerie_bricolage",
                "parfumerie",
                "horlogerie_bijouterie",
                "fleuriste",
                "magasin_d_optique",
                "station_service",
            ]
        ),
        "hypermarche": valeur_entier(donnees, "hypermarche"),
        "supermarche": valeur_entier(donnees, "supermarche"),
        "superette": valeur_entier(donnees, "superette"),
        "epicerie": valeur_entier(donnees, "epicerie"),
        "boulangerie": valeur_entier(donnees, "boulangerie"),
        "boucherie_charcuterie": valeur_entier(donnees, "boucherie_charcuterie"),
        "poissonnerie": valeur_entier(donnees, "poissonnerie"),
        "fleuriste": valeur_entier(donnees, "fleuriste"),
        "magasin_d_optique": valeur_entier(donnees, "magasin_d_optique"),
        "station_service": valeur_entier(donnees, "station_service"),
        "lat": geo_point.get("lat"),
        "lon": geo_point.get("lon"),
    }


@lru_cache(maxsize=1)
def charger_commerces_paris() -> tuple[dict[str, Any], ...]:
    try:
        response = requests.get(
            COMMERCES_PARIS_API_URL,
            params={
                "where": "departement=75",
                "limit": 20,
                "order_by": "departement_commune",
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de récupérer les commerces parisiens",
        ) from exc

    payload = response.json()
    commerces = [
        normaliser_commerce_arrondissement(resultat)
        for resultat in payload.get("results", [])
    ]
    if not commerces:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aucune donnée commerce disponible pour Paris",
        )

    densite_max = max(
        commerce["commerces_pour_10000_habitants"] or 0 for commerce in commerces
    )
    for commerce in commerces:
        densite = commerce["commerces_pour_10000_habitants"] or 0
        commerce["note_commerces_sur_10"] = (
            round(densite / densite_max * 10, 1) if densite_max else None
        )

    return tuple(sorted(commerces, key=lambda item: item["arrondissement"]))

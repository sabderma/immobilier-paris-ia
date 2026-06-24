from __future__ import annotations

import json
import logging
import os
import time
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from api.core import CHAMPS_COMMERCES, COMMERCES_PARIS_API_URL


logger = logging.getLogger("immobilier_paris.api")

CRITERES_SCORE_ARRONDISSEMENT = {
    "score_proximite_quotidienne_sur_10": (
        "commerces_alimentaires_pour_10000_habitants",
        0.45,
    ),
    "score_diversite_commerciale_sur_10": (
        "commerces_specialises_pour_10000_habitants",
        0.35,
    ),
    "score_grandes_surfaces_sur_10": (
        "grandes_surfaces_pour_10000_habitants",
        0.20,
    ),
}
SCORE_MINIMUM_ARRONDISSEMENT = 4.0
SCORE_MAXIMUM_ARRONDISSEMENT = 10.0


def lire_float_env(nom: str, valeur_defaut: float) -> float:
    try:
        return float(os.getenv(nom, str(valeur_defaut)))
    except ValueError:
        logger.warning(
            "invalid_float_environment_variable",
            extra={"environment_variable": nom, "default": valeur_defaut},
        )
        return valeur_defaut


TIMEOUT_COMMERCES_SECONDES = lire_float_env("COMMERCES_API_TIMEOUT_SECONDS", 5.0)
TTL_CACHE_COMMERCES_SUCCES_SECONDES = lire_float_env(
    "COMMERCES_CACHE_SUCCESS_TTL_SECONDS",
    3600.0,
)
TTL_CACHE_COMMERCES_ECHEC_SECONDES = lire_float_env(
    "COMMERCES_CACHE_FAILURE_TTL_SECONDS",
    60.0,
)
COMMERCES_CACHE_PATH = Path(
    os.getenv(
        "COMMERCES_PARIS_CACHE_PATH",
        "/tmp/immobilier_paris_commerces_cache.json",
    )
)
_CACHE_COMMERCES: tuple[dict[str, Any], ...] | None = None
_CACHE_COMMERCES_EXPIRE_AT = 0.0


def valeur_entier(donnees: dict[str, Any], champ: str) -> int:
    valeur = donnees.get(champ)
    if valeur is None or pd.isna(valeur):
        return 0
    return int(valeur)


def densite_pour_10000(nombre: int, population: int) -> float | None:
    return round(nombre / population * 10000, 1) if population else None


def arrondir_score(score: float) -> float:
    return float(Decimal(str(score)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def scores_progressifs(valeurs: list[float]) -> list[float]:
    """Répartit les scores entre 4 et 10 selon le classement relatif."""
    if len(valeurs) <= 1:
        return [SCORE_MAXIMUM_ARRONDISSEMENT for _valeur in valeurs]

    rangs = pd.Series(valeurs).rank(method="average", ascending=True)
    amplitude = SCORE_MAXIMUM_ARRONDISSEMENT - SCORE_MINIMUM_ARRONDISSEMENT
    return [
        arrondir_score(
            SCORE_MINIMUM_ARRONDISSEMENT
            + ((float(rang) - 1) / (len(valeurs) - 1)) * amplitude,
        )
        for rang in rangs
    ]


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
    grandes_surfaces = sum(
        valeur_entier(donnees, champ)
        for champ in [
            "hypermarche",
            "supermarche",
            "grande_surface_de_bricolage",
        ]
    )
    commerces_alimentaires = sum(
        valeur_entier(donnees, champ)
        for champ in [
            "superette",
            "epicerie",
            "boulangerie",
            "boucherie_charcuterie",
            "produits_surgeles",
            "poissonnerie",
        ]
    )
    commerces_specialises = sum(
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
    )
    geo_point = donnees.get("geo_point_2d") or {}

    return {
        "arrondissement": departement_commune - 75100,
        "departement_commune": departement_commune,
        "nom_arrondissement": nom_arrondissement(donnees),
        "population_2010": population,
        "total_commerces": total_commerces,
        "commerces_pour_10000_habitants": densite_pour_10000(
            total_commerces,
            population,
        ),
        "grandes_surfaces": grandes_surfaces,
        "grandes_surfaces_pour_10000_habitants": densite_pour_10000(
            grandes_surfaces,
            population,
        ),
        "commerces_alimentaires": commerces_alimentaires,
        "commerces_alimentaires_pour_10000_habitants": densite_pour_10000(
            commerces_alimentaires,
            population,
        ),
        "commerces_specialises": commerces_specialises,
        "commerces_specialises_pour_10000_habitants": densite_pour_10000(
            commerces_specialises,
            population,
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


def charger_timeout_commerces() -> tuple[float, float]:
    timeout = max(1.0, TIMEOUT_COMMERCES_SECONDES)
    return 2.0, timeout


def charger_cache_disque_commerces() -> list[dict[str, Any]]:
    if not COMMERCES_CACHE_PATH.exists():
        return []

    try:
        payload = json.loads(COMMERCES_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "commerces_cache_unavailable",
            extra={"cache_path": str(COMMERCES_CACHE_PATH), "error": str(exc)},
        )
        return []

    resultats = payload.get("results", []) if isinstance(payload, dict) else payload
    if not isinstance(resultats, list):
        return []
    return [resultat for resultat in resultats if isinstance(resultat, dict)]


def sauvegarder_cache_disque_commerces(resultats: list[dict[str, Any]]) -> None:
    try:
        COMMERCES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        COMMERCES_CACHE_PATH.write_text(
            json.dumps({"results": resultats}, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning(
            "commerces_cache_write_failed",
            extra={"cache_path": str(COMMERCES_CACHE_PATH), "error": str(exc)},
        )


def recuperer_resultats_commerces() -> tuple[list[dict[str, Any]], str]:
    try:
        response = requests.get(
            COMMERCES_PARIS_API_URL,
            params={
                "where": "departement=75",
                "limit": 20,
                "order_by": "departement_commune",
            },
            timeout=charger_timeout_commerces(),
        )
        response.raise_for_status()
        payload = response.json()
        resultats = [
            resultat
            for resultat in payload.get("results", [])
            if isinstance(resultat, dict)
        ]
        if resultats:
            sauvegarder_cache_disque_commerces(resultats)
            return resultats, "open_data"
        logger.warning("commerces_open_data_empty")
    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            "commerces_open_data_unavailable",
            extra={"error": str(exc), "timeout_seconds": TIMEOUT_COMMERCES_SECONDES},
        )

    resultats_cache = charger_cache_disque_commerces()
    if resultats_cache:
        return resultats_cache, "cache_local"
    return [], "indisponible"


def normaliser_liste_commerces(
    resultats: list[dict[str, Any]],
    source_donnees: str,
) -> tuple[dict[str, Any], ...]:
    commerces = [
        normaliser_commerce_arrondissement(resultat)
        for resultat in resultats
    ]
    if not commerces:
        return tuple()

    for champ_score, (
        champ_densite,
        _ponderation,
    ) in CRITERES_SCORE_ARRONDISSEMENT.items():
        scores = scores_progressifs(
            [float(commerce[champ_densite] or 0) for commerce in commerces]
        )
        for commerce, score in zip(commerces, scores):
            commerce[champ_score] = score

    for commerce in commerces:
        score_arrondissement = sum(
            commerce[champ_score] * ponderation
            for champ_score, (
                _champ_densite,
                ponderation,
            ) in CRITERES_SCORE_ARRONDISSEMENT.items()
        )
        commerce["score_arrondissement_sur_10"] = arrondir_score(score_arrondissement)
        commerce["source_donnees"] = source_donnees

    return tuple(sorted(commerces, key=lambda item: item["arrondissement"]))


def charger_commerces_paris() -> tuple[dict[str, Any], ...]:
    global _CACHE_COMMERCES, _CACHE_COMMERCES_EXPIRE_AT

    if _CACHE_COMMERCES is not None and time.monotonic() < _CACHE_COMMERCES_EXPIRE_AT:
        return _CACHE_COMMERCES

    resultats, source_donnees = recuperer_resultats_commerces()
    commerces = normaliser_liste_commerces(resultats, source_donnees)
    _CACHE_COMMERCES = commerces
    ttl = (
        TTL_CACHE_COMMERCES_SUCCES_SECONDES
        if commerces
        else TTL_CACHE_COMMERCES_ECHEC_SECONDES
    )
    _CACHE_COMMERCES_EXPIRE_AT = time.monotonic() + max(1.0, ttl)
    return commerces


def vider_cache_commerces() -> None:
    global _CACHE_COMMERCES, _CACHE_COMMERCES_EXPIRE_AT
    _CACHE_COMMERCES = None
    _CACHE_COMMERCES_EXPIRE_AT = 0.0


charger_commerces_paris.cache_clear = vider_cache_commerces  # type: ignore[attr-defined]

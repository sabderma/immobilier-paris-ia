from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI, OpenAIError

from api.core import charger_env


MODELE_RESUME_LIEU_PAR_DEFAUT = "gpt-5.4-mini"
TIMEOUT_OPENAI_SECONDES = 25
INSTRUCTIONS_RESUME_LIEU = """
Tu rédiges en français un résumé court et professionnel d'un secteur parisien.
Utilise uniquement les données fournies par l'application.
Décris en 2 ou 3 phrases l'accès aux transports et les services du quotidien
dans le rayon indiqué. Tu peux citer les lieux les plus proches lorsqu'ils sont
fournis. N'invente rien sur la sécurité, le calme, les prix immobiliers, la
qualité de vie ou des lieux absents des données. Reste neutre et factuel.
""".strip()


def _lieux_proches(
    lieux: list[dict[str, Any]],
    categorie: str | None = None,
    limite: int = 5,
) -> list[dict[str, Any]]:
    selection = [
        lieu
        for lieu in lieux
        if categorie is None or lieu.get("categorie") == categorie
    ]
    return [
        {
            "nom": lieu.get("nom"),
            "type": lieu.get("sous_categorie"),
            "modes": lieu.get("modes"),
            "lignes": lieu.get("lignes"),
            "distance_metres": lieu.get("distance_metres"),
        }
        for lieu in selection[:limite]
    ]


def construire_donnees_resume(
    adresse_normalisee: str,
    proximite: dict[str, Any],
) -> dict[str, Any]:
    equipements = proximite.get("equipements") or []
    return {
        "adresse_normalisee": adresse_normalisee,
        "rayon_metres": proximite.get("rayon_metres", 500),
        "methode_distance": proximite.get("distance", "à vol d'oiseau"),
        "totaux": proximite.get("totaux") or {},
        "transports_les_plus_proches": _lieux_proches(
            proximite.get("transports") or [],
        ),
        "commerces_les_plus_proches": _lieux_proches(equipements, "commerce"),
        "ecoles_les_plus_proches": _lieux_proches(equipements, "education"),
        "sante_les_plus_proches": _lieux_proches(equipements, "sante"),
    }


def generer_resume_lieu(
    adresse_normalisee: str,
    proximite: dict[str, Any],
) -> dict[str, str]:
    charger_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"erreur": "Le résumé OpenAI n'est pas configuré."}

    modele = os.getenv("OPENAI_MODEL", MODELE_RESUME_LIEU_PAR_DEFAUT)
    donnees = construire_donnees_resume(adresse_normalisee, proximite)

    try:
        client = OpenAI(
            api_key=api_key,
            timeout=TIMEOUT_OPENAI_SECONDES,
            max_retries=1,
        )
        response = client.responses.create(
            model=modele,
            reasoning={"effort": "none"},
            instructions=INSTRUCTIONS_RESUME_LIEU,
            input=json.dumps(donnees, ensure_ascii=False),
            max_output_tokens=220,
            store=False,
        )
        texte = response.output_text.strip()
    except (OpenAIError, ValueError) as exc:
        return {"erreur": f"Le résumé OpenAI est temporairement indisponible : {exc}"}

    if not texte:
        return {"erreur": "OpenAI n'a pas retourné de résumé."}

    return {
        "texte": texte,
        "modele": modele,
        "source": "OpenAI",
    }

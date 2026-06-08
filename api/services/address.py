from __future__ import annotations

import json
import os
import re
from typing import Any

from fastapi import HTTPException, status

from api.core import charger_env
from api.schemas import GEMINI_ADRESSE_SCORE_SCHEMA


def adresse_hors_paris(adresse: str) -> bool:
    codes_postaux = re.findall(r"\b\d{5}\b", adresse)
    return bool(codes_postaux) and not any(code.startswith("75") for code in codes_postaux)


def arrondissement_dans_adresse(adresse: str) -> int | None:
    code_postal = re.search(r"\b750([1-9]|1[0-9]|20)\b", adresse)
    if code_postal:
        return int(code_postal.group(1))

    paris_arrondissement = re.search(
        r"\bparis\s*([1-9]|1[0-9]|20)\s*(?:e|er|eme|ème)?\b",
        adresse,
        flags=re.IGNORECASE,
    )
    if paris_arrondissement:
        return int(paris_arrondissement.group(1))

    return None


def normaliser_adresse_paris(adresse: str, arrondissement: int | None = None) -> str:
    adresse_nettoyee = " ".join(adresse.strip().rstrip(",").split())
    if "paris" in adresse_nettoyee.lower():
        return adresse_nettoyee
    if arrondissement is None:
        return adresse_nettoyee
    return f"{adresse_nettoyee}, Paris {arrondissement}"


def construire_prompt_score_adresse(adresse: str, arrondissement: int | None) -> str:
    arrondissement_texte = f"Paris {arrondissement}" if arrondissement else "non fourni"
    return f"""
Tu es un assistant specialise dans l'analyse de localisation immobiliere a Paris.

Objectif :
Analyser une adresse exacte situee uniquement a Paris et produire un score
d'emplacement immobilier sur 100.

Adresse a analyser :
{adresse}

Arrondissement detecte :
{arrondissement_texte}

Regles obligatoires :
- Tu dois accepter uniquement les adresses situees a Paris intra-muros.
- Si l'adresse n'est pas a Paris, retourne uniquement ce JSON :
  {{"erreur": "Adresse non valide", "message": "Il faut saisir une adresse situee a Paris."}}
- Si l'adresse ne precise pas Paris, un code postal 75001 a 75020, ou un arrondissement parisien,
  retourne uniquement ce JSON :
  {{"erreur": "Adresse incomplète", "message": "Il faut saisir une adresse complète avec Paris et l'arrondissement."}}
- Ne jamais analyser une adresse hors Paris.
- Ne jamais ecrire "a verifier", "à vérifier" ou une distance vide.
- Pour chaque lieu trouve, donne une distance exacte si tu la connais, sinon une distance approximative.
- Les distances doivent etre ecrites comme "120 m", "environ 300 m" ou "environ 8 min a pied".
- Donne les noms concrets des stations, lignes de transport, ecoles, commerces, espaces verts et services de sante.
- Si tu ne connais pas assez d'elements dans une categorie, mets moins d'elements, mais ne les invente pas.
- Reponds uniquement en JSON valide, sans texte avant ou apres.

Analyse les categories suivantes :
1. Transports a proximite
2. Commerces et supermarches
3. Ecoles
4. Espaces verts
5. Sante
6. Zones touristiques ou tres frequentees
7. Tranquillite
8. Attractivite immobiliere

Pour chaque categorie :
- donne un score sur 100
- donne le nombre d'elements trouves
- donne les noms precis
- donne les distances exactes ou approximatives
- donne un commentaire utile pour un acheteur immobilier
""".strip()


def extraire_json_gemini(texte: str) -> dict[str, Any]:
    contenu = texte.strip()
    if contenu.startswith("```"):
        contenu = re.sub(r"^```(?:json)?", "", contenu, flags=re.IGNORECASE).strip()
        contenu = re.sub(r"```$", "", contenu).strip()

    try:
        return json.loads(contenu)
    except json.JSONDecodeError:
        debut = contenu.find("{")
        fin = contenu.rfind("}")
        if debut == -1 or fin == -1 or fin <= debut:
            raise
        return json.loads(contenu[debut : fin + 1])


def generer_score_adresse_gemini(
    adresse: str,
    arrondissement: int | None,
) -> dict[str, Any]:
    charger_env()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY n'est pas configurée dans le fichier .env",
        )

    try:
        from google import genai
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La dépendance google-genai est manquante. Réinstallez requirements.txt.",
        ) from exc

    prompt = construire_prompt_score_adresse(adresse, arrondissement)
    modele = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=modele,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": GEMINI_ADRESSE_SCORE_SCHEMA,
            },
        )
        resultat = extraire_json_gemini(response.text or "")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Impossible de générer la note avec Gemini : {exc}",
        ) from exc

    return resultat

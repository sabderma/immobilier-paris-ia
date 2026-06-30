"""Collecte brute des commerces parisiens depuis une API REST.

Ce script appelle l'API open data, garde les parametres de la requete et ecrit
la reponse brute dans `data/raw/api/`. Il sert de preuve C1 pour la source API.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
COMMERCES_PARIS_API_URL = (
    "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/"
    "les-commerces-par-commune-ou-arrondissement-base-permanente-des-equipements/"
    "records"
)
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/raw/api/commerces_paris_open_data.json"


def maintenant_iso() -> str:
    """Retourne la date de collecte pour tracer le fichier produit."""

    return datetime.now(timezone.utc).isoformat()


def construire_payload_brut(
    *,
    url: str,
    params: dict[str, Any],
    status_code: int | None,
    data: dict[str, Any] | None,
    dry_run: bool,
) -> dict[str, Any]:
    """Construit le JSON sauvegarde, avec les infos de source et de requete."""

    return {
        "source": "Open Data Ile-de-France - Base permanente des equipements 2012",
        "url": url,
        "params": params,
        "collecte_le": maintenant_iso(),
        "mode": "dry-run" if dry_run else "execution",
        "status_code": status_code,
        "data": data,
    }


def collecter_commerces_paris(
    *,
    output_path: Path,
    timeout: float,
    limit: int,
    dry_run: bool,
) -> None:
    """Lance la requete API et sauvegarde la reponse brute en JSON."""

    params = {
        "where": "departement=75",
        "limit": limit,
        "order_by": "departement_commune",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        # En mode simulation, on ecrit seulement ce qui aurait ete appele.
        payload = construire_payload_brut(
            url=COMMERCES_PARIS_API_URL,
            params=params,
            status_code=None,
            data=None,
            dry_run=True,
        )
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return

    response = requests.get(
        COMMERCES_PARIS_API_URL,
        params=params,
        timeout=(2.0, timeout),
    )
    # Si l'API renvoie une erreur HTTP, le script s'arrete clairement.
    response.raise_for_status()

    payload = construire_payload_brut(
        url=COMMERCES_PARIS_API_URL,
        params=params,
        status_code=response.status_code,
        data=response.json(),
        dry_run=False,
    )
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def construire_parser() -> argparse.ArgumentParser:
    """Declare les options possibles pour relancer la collecte API."""

    parser = argparse.ArgumentParser(
        description="Collecte brute des donnees commerces Paris depuis une API REST.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Fichier JSON brut de sortie.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        help="Timeout de lecture de l'API en secondes.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Nombre maximal d'enregistrements a recuperer.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ecrit seulement les parametres de collecte, sans appeler l'API.",
    )
    return parser


def main() -> int:
    """Point d'entree du script de collecte API."""

    args = construire_parser().parse_args()
    collecter_commerces_paris(
        output_path=args.output,
        timeout=max(1.0, args.timeout),
        limit=max(1, args.limit),
        dry_run=args.dry_run,
    )
    print(f"Collecte API commerces Paris terminee: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

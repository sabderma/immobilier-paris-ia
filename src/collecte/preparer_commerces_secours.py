"""Prepare un fichier local de secours depuis la collecte API commerces.

La collecte brute reste dans `data/raw/api/`. Ce script lit ce brut, extrait les
resultats utilisables et fabrique un JSON final pour l'application.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT_DIR / "data/raw/api/commerces_paris_open_data.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/final/commerces_paris_secours.json"


def maintenant_iso() -> str:
    """Retourne la date de generation du snapshot de secours."""

    return datetime.now(timezone.utc).isoformat()


def charger_resultats_api(input_path: Path) -> list[dict[str, Any]]:
    """Lit le JSON brut de l'API et recupere la liste des resultats."""

    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Le fichier d'entree doit contenir un objet JSON.")

    data = payload.get("data")
    if isinstance(data, dict):
        resultats = data.get("results", [])
    else:
        resultats = payload.get("results", [])

    if not isinstance(resultats, list):
        raise ValueError("Le fichier d'entree ne contient pas de liste results.")

    commerces = [resultat for resultat in resultats if isinstance(resultat, dict)]
    if not commerces:
        raise ValueError("Aucun commerce exploitable trouve dans le fichier brut.")

    return commerces


def construire_snapshot(
    resultats: list[dict[str, Any]],
    *,
    input_path: Path,
) -> dict[str, Any]:
    """Construit le JSON final avec la source et le nombre de resultats."""

    return {
        "source": "Snapshot local de secours genere depuis Open Data Ile-de-France",
        "genere_le": maintenant_iso(),
        "source_brute": str(input_path.relative_to(ROOT_DIR)),
        "nombre_resultats": len(resultats),
        "results": resultats,
    }


def ecrire_json_atomique(output_path: Path, payload: dict[str, Any]) -> None:
    """Ecrit le JSON via un fichier temporaire pour eviter un fichier coupe."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp_path.replace(output_path)


def preparer_snapshot_secours(input_path: Path, output_path: Path) -> None:
    """Transforme la collecte API brute en snapshot local utilisable."""

    resultats = charger_resultats_api(input_path)
    snapshot = construire_snapshot(resultats, input_path=input_path)
    ecrire_json_atomique(output_path, snapshot)


def construire_parser() -> argparse.ArgumentParser:
    """Declare les options pour choisir les fichiers d'entree et sortie."""

    parser = argparse.ArgumentParser(
        description=(
            "Prepare le snapshot final de secours des commerces depuis la "
            "collecte API brute."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Fichier JSON brut produit par la collecte API.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Fichier final de secours utilise par l'application.",
    )
    return parser


def main() -> int:
    """Point d'entree du script de preparation du snapshot."""

    args = construire_parser().parse_args()
    preparer_snapshot_secours(args.input, args.output)
    print(f"Snapshot commerces de secours genere: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

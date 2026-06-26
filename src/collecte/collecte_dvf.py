from __future__ import annotations

import argparse
import gzip
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data/raw/DVF"
DEFAULT_REPORT_PATH = ROOT_DIR / "data/raw/collecte/rapport_dvf.json"
DEFAULT_YEARS = (2021, 2022, 2023, 2024, 2025)
DEFAULT_DEPARTMENT = "75"
GEO_DVF_URL_TEMPLATE = (
    "https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/{department}.csv.gz"
)
EXPECTED_COLUMNS = {
    "id_mutation",
    "date_mutation",
    "nature_mutation",
    "valeur_fonciere",
    "code_departement",
    "code_postal",
    "type_local",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "longitude",
    "latitude",
}


@dataclass
class DvfResult:
    annee: int
    fichier: str
    source_url: str
    statut: str
    lignes: int
    colonnes_ok: bool
    telecharge: bool
    message: str


def afficher_chemin(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compter_lignes(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as file:
        return max(sum(1 for _line in file) - 1, 0)


def verifier_colonnes(path: Path) -> bool:
    with path.open("r", encoding="utf-8", errors="replace") as file:
        header = file.readline().strip().split(",")
    return EXPECTED_COLUMNS.issubset(set(header))


def telecharger_csv_gzip(url: str, output_path: Path, timeout: float) -> None:
    response = requests.get(url, stream=True, timeout=(3.0, timeout))
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(delete=False, suffix=".csv", dir=output_path.parent) as tmp:
        tmp_path = Path(tmp.name)
        with gzip.GzipFile(fileobj=response.raw) as gzip_file:
            shutil.copyfileobj(gzip_file, tmp)

    tmp_path.replace(output_path)


def traiter_annee(
    annee: int,
    *,
    department: str,
    output_dir: Path,
    timeout: float,
    force: bool,
    dry_run: bool,
) -> DvfResult:
    output_path = output_dir / f"{department}-{annee}.csv"
    source_url = GEO_DVF_URL_TEMPLATE.format(year=annee, department=department)

    if output_path.exists() and not force:
        lignes = compter_lignes(output_path)
        colonnes_ok = verifier_colonnes(output_path)
        statut = "ok" if lignes > 0 and colonnes_ok else "erreur"
        message = "fichier local deja present"
        return DvfResult(
            annee=annee,
            fichier=afficher_chemin(output_path),
            source_url=source_url,
            statut=statut,
            lignes=lignes,
            colonnes_ok=colonnes_ok,
            telecharge=False,
            message=message,
        )

    if dry_run:
        return DvfResult(
            annee=annee,
            fichier=afficher_chemin(output_path),
            source_url=source_url,
            statut="dry-run",
            lignes=0,
            colonnes_ok=False,
            telecharge=False,
            message="telechargement simule",
        )

    telecharger_csv_gzip(source_url, output_path, timeout)
    lignes = compter_lignes(output_path)
    colonnes_ok = verifier_colonnes(output_path)
    statut = "ok" if lignes > 0 and colonnes_ok else "erreur"
    return DvfResult(
        annee=annee,
        fichier=afficher_chemin(output_path),
        source_url=source_url,
        statut=statut,
        lignes=lignes,
        colonnes_ok=colonnes_ok,
        telecharge=True,
        message="fichier telecharge",
    )


def ecrire_rapport(resultats: list[DvfResult], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "genere_le": maintenant_iso(),
        "source": "Geo-DVF - fichiers CSV par departement",
        "statut_global": (
            "ok"
            if all(resultat.statut in {"ok", "dry-run"} for resultat in resultats)
            else "erreur"
        ),
        "resultats": [asdict(resultat) for resultat in resultats],
    }
    import json

    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collecte ou verifie les fichiers bruts Geo-DVF de Paris.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(DEFAULT_YEARS),
        help="Annees DVF a collecter ou verifier.",
    )
    parser.add_argument(
        "--department",
        default=DEFAULT_DEPARTMENT,
        help="Code departement a collecter.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Dossier des fichiers CSV bruts DVF.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Timeout de lecture pour chaque telechargement.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Rapport JSON de verification DVF.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Retelecharge les fichiers meme s'ils existent deja.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les actions sans telecharger.",
    )
    return parser


def main() -> int:
    args = construire_parser().parse_args()
    resultats = [
        traiter_annee(
            annee,
            department=args.department,
            output_dir=args.output_dir,
            timeout=max(1.0, args.timeout),
            force=args.force,
            dry_run=args.dry_run,
        )
        for annee in args.years
    ]
    ecrire_rapport(resultats, args.report)

    for resultat in resultats:
        print(
            f"DVF {resultat.annee}: {resultat.statut} - "
            f"{resultat.fichier} ({resultat.lignes} lignes)"
        )

    return 0 if all(resultat.statut in {"ok", "dry-run"} for resultat in resultats) else 1


if __name__ == "__main__":
    raise SystemExit(main())

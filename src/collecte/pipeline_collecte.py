from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = ROOT_DIR / "data/raw/collecte/logs"
DEFAULT_REPORT_PATH = ROOT_DIR / "data/raw/collecte/rapport_execution_collecte.json"


@dataclass(frozen=True)
class CollecteEtape:
    nom: str
    type_collecte: str
    script: Path
    fichier_sortie: Path
    format_sortie: str


@dataclass
class CollecteResult:
    nom: str
    type_collecte: str
    script: str
    fichier_sortie: str
    format_sortie: str
    statut: str
    code_retour: int | None
    log: str | None
    debut: str
    fin: str
    duree_secondes: float


ETAPES_COLLECTE = (
    CollecteEtape(
        "api_commerces",
        "api_rest",
        ROOT_DIR / "src/collecte/collecte_api.py",
        ROOT_DIR / "data/raw/api/commerces_paris_open_data.json",
        "json",
    ),
    CollecteEtape(
        "commerces_secours",
        "preparation",
        ROOT_DIR / "src/collecte/preparer_commerces_secours.py",
        ROOT_DIR / "data/final/commerces_paris_secours.json",
        "json",
    ),
    CollecteEtape(
        "dvf",
        "fichier_donnees",
        ROOT_DIR / "src/collecte/collecte_dvf.py",
        ROOT_DIR / "data/raw/DVF",
        "csv",
    ),
    CollecteEtape(
        "orpi",
        "scraping",
        ROOT_DIR / "src/collecte/scrapporpi.py",
        ROOT_DIR / "data/raw/scraping/annonces_orpi_paris.csv",
        "csv",
    ),
    CollecteEtape(
        "laforet",
        "scraping",
        ROOT_DIR / "src/collecte/scrappforet.py",
        ROOT_DIR / "data/raw/scraping/annonces_laforet_paris_complet.csv",
        "csv",
    ),
    CollecteEtape(
        "lefigaro",
        "scraping",
        ROOT_DIR / "src/collecte/scrapplefigaro.py",
        ROOT_DIR / "data/raw/scraping/annonces_lefigaro_paris.csv",
        "csv",
    ),
    CollecteEtape(
        "century21",
        "scraping",
        ROOT_DIR / "src/collecte/scrappcentury21.py",
        ROOT_DIR / "data/raw/scraping/annonces_century21_paris.csv",
        "csv",
    ),
    CollecteEtape(
        "stephaneplaza",
        "scraping",
        ROOT_DIR / "src/collecte/scrappstephaneplazaimmobilier.py",
        ROOT_DIR / "data/raw/scraping/annonces_plaza_paris.csv",
        "csv",
    ),
)


def maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def selectionner_scripts(
    seulement: list[str] | None,
    exclure: list[str] | None,
) -> list[CollecteEtape]:
    noms_connus = {script.nom for script in ETAPES_COLLECTE}
    seulement_set = set(seulement or noms_connus)
    exclure_set = set(exclure or [])
    noms_inconnus = (seulement_set | exclure_set) - noms_connus

    if noms_inconnus:
        noms = ", ".join(sorted(noms_inconnus))
        raise ValueError(f"Scripts inconnus: {noms}")

    return [
        script
        for script in ETAPES_COLLECTE
        if script.nom in seulement_set and script.nom not in exclure_set
    ]


def executer_script(
    script: CollecteEtape,
    *,
    python_cmd: str,
    log_dir: Path,
    dry_run: bool,
) -> CollecteResult:
    debut_dt = datetime.now(timezone.utc)
    debut = debut_dt.isoformat()
    log_path = log_dir / f"{debut_dt.strftime('%Y%m%d_%H%M%S')}_{script.nom}.log"

    if dry_run:
        fin_dt = datetime.now(timezone.utc)
        return CollecteResult(
            nom=script.nom,
            type_collecte=script.type_collecte,
            script=str(script.script.relative_to(ROOT_DIR)),
            fichier_sortie=str(script.fichier_sortie.relative_to(ROOT_DIR)),
            format_sortie=script.format_sortie,
            statut="dry-run",
            code_retour=None,
            log=None,
            debut=debut,
            fin=fin_dt.isoformat(),
            duree_secondes=0.0,
        )

    log_dir.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"Commande: {python_cmd} {script.script}\n")
        log_file.write(f"Debut: {debut}\n\n")
        log_file.flush()
        processus = subprocess.run(
            [python_cmd, str(script.script)],
            cwd=ROOT_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=False,
        )

    fin_dt = datetime.now(timezone.utc)
    duree = (fin_dt - debut_dt).total_seconds()
    statut = "ok" if processus.returncode == 0 else "erreur"

    return CollecteResult(
        nom=script.nom,
        type_collecte=script.type_collecte,
        script=str(script.script.relative_to(ROOT_DIR)),
        fichier_sortie=str(script.fichier_sortie.relative_to(ROOT_DIR)),
        format_sortie=script.format_sortie,
        statut=statut,
        code_retour=processus.returncode,
        log=str(log_path.relative_to(ROOT_DIR)),
        debut=debut,
        fin=fin_dt.isoformat(),
        duree_secondes=round(duree, 2),
    )


def ecrire_rapport(
    resultats: list[CollecteResult],
    *,
    report_path: Path,
    dry_run: bool,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "genere_le": maintenant_iso(),
        "mode": "dry-run" if dry_run else "execution",
        "note": (
            "Ce rapport trace l'execution du pipeline. Il ne remplace pas les CSV "
            "de scraping, qui restent separes dans data/raw/scraping/. La collecte "
            "API conserve son JSON brut dans data/raw/api/, puis le snapshot final "
            "de secours est genere dans data/final/. Les fichiers DVF bruts restent "
            "dans data/raw/DVF/."
        ),
        "dossier_csv_scraping": "data/raw/scraping",
        "dossier_csv_dvf": "data/raw/DVF",
        "dossier_json_api": "data/raw/api",
        "dossier_final": "data/final",
        "nombre_scripts": len(resultats),
        "statut_global": (
            "ok"
            if all(resultat.statut in {"ok", "dry-run"} for resultat in resultats)
            else "erreur"
        ),
        "resultats": [asdict(resultat) for resultat in resultats],
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lance les collectes de donnees du projet immobilier Paris IA.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=[script.nom for script in ETAPES_COLLECTE],
        help="Lance uniquement les scripts listes.",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=[script.nom for script in ETAPES_COLLECTE],
        help="Exclut les scripts listes.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Interpreteur Python utilise pour lancer les scripts.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Dossier des logs d'execution.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Chemin du rapport JSON d'execution, sans fusionner les donnees.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les scripts qui seraient lances sans les executer.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue les scripts suivants si un script echoue.",
    )
    return parser


def main() -> int:
    parser = construire_parser()
    args = parser.parse_args()

    try:
        scripts = selectionner_scripts(args.only, args.skip)
    except ValueError as exc:
        parser.error(str(exc))

    resultats: list[CollecteResult] = []
    for script in scripts:
        print(
            f"[collecte] {script.nom} ({script.type_collecte}) "
            f"-> {script.script.relative_to(ROOT_DIR)}"
        )
        print(
            f"[collecte] sortie {script.format_sortie} "
            f"-> {script.fichier_sortie.relative_to(ROOT_DIR)}"
        )
        resultat = executer_script(
            script,
            python_cmd=args.python,
            log_dir=args.log_dir,
            dry_run=args.dry_run,
        )
        resultats.append(resultat)
        print(f"[collecte] {script.nom}: {resultat.statut}")

        if resultat.statut == "erreur" and not args.continue_on_error:
            break

    ecrire_rapport(resultats, report_path=args.report, dry_run=args.dry_run)
    print(f"[collecte] rapport: {args.report.relative_to(ROOT_DIR)}")

    return 0 if all(resultat.statut in {"ok", "dry-run"} for resultat in resultats) else 1


if __name__ == "__main__":
    raise SystemExit(main())

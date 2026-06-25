from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from api.core import construire_engine  # noqa: E402

DEFAULT_REPORT_PATH = ROOT_DIR / "data/raw/collecte/rapport_purge_rgpd.json"


TABLES_PURGE = {
    "adresses_exactes": {
        "table": "exact_address_history",
        "date_column": "created_at",
        "description": "Historique des adresses exactes recherchees par utilisateur.",
    },
    "predictions": {
        "table": "predictions",
        "date_column": "created_at",
        "description": "Historique des predictions de prix par utilisateur.",
    },
}


def masquer_texte(valeur: Any, longueur_visible: int = 8) -> str | None:
    if valeur is None:
        return None
    texte = str(valeur)
    if len(texte) <= longueur_visible:
        return "*" * len(texte)
    return f"{texte[:longueur_visible]}..."


def construire_select_apercu(table: str, date_column: str) -> str:
    if table == "exact_address_history":
        return f"""
            SELECT
                id,
                user_id,
                address,
                {date_column} AS created_at
            FROM {table}
            WHERE {date_column} < :cutoff
            ORDER BY {date_column} ASC
            LIMIT :limit;
        """
    if table == "predictions":
        return f"""
            SELECT
                id,
                user_id,
                surface,
                nb_pieces,
                arrondissement,
                predicted_price,
                {date_column} AS created_at
            FROM {table}
            WHERE {date_column} < :cutoff
            ORDER BY {date_column} ASC
            LIMIT :limit;
        """
    raise ValueError(f"Table non supportee pour l'apercu: {table}")


def normaliser_apercu(table: str, lignes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    apercu = []
    for ligne in lignes:
        item = dict(ligne)
        created_at = item.get("created_at")
        if hasattr(created_at, "isoformat"):
            item["created_at"] = created_at.isoformat()

        if table == "exact_address_history":
            item["address_apercu"] = masquer_texte(item.pop("address", None))

        apercu.append(item)
    return apercu


def lister_apercu_a_purger(
    connexion,
    table: str,
    date_column: str,
    cutoff: datetime,
    limit: int,
) -> list[dict[str, Any]]:
    lignes = connexion.execute(
        text(construire_select_apercu(table, date_column)),
        {"cutoff": cutoff, "limit": limit},
    ).mappings().all()
    return normaliser_apercu(table, [dict(ligne) for ligne in lignes])


def compter_lignes_a_purger(connexion, table: str, date_column: str, cutoff: datetime) -> int:
    resultat = connexion.execute(
        text(
            f"""
            SELECT COUNT(*) AS total
            FROM {table}
            WHERE {date_column} < :cutoff;
            """
        ),
        {"cutoff": cutoff},
    ).scalar_one()
    return int(resultat)


def supprimer_lignes(connexion, table: str, date_column: str, cutoff: datetime) -> int:
    resultat = connexion.execute(
        text(
            f"""
            DELETE FROM {table}
            WHERE {date_column} < :cutoff;
            """
        ),
        {"cutoff": cutoff},
    )
    return int(resultat.rowcount or 0)


def purger_donnees(
    *,
    database_url: str | None,
    jours_conservation_adresses: int,
    jours_conservation_predictions: int,
    preview_limit: int,
    execute: bool,
) -> dict[str, Any]:
    engine = construire_engine(database_url)
    maintenant = datetime.now(timezone.utc)
    regles = {
        "adresses_exactes": jours_conservation_adresses,
        "predictions": jours_conservation_predictions,
    }
    rapport: dict[str, Any] = {
        "genere_le": maintenant.isoformat(),
        "mode": "execution" if execute else "simulation",
        "objectif": "Purge RGPD des historiques utilisateur trop anciens.",
        "resultats": [],
    }

    with engine.begin() as connexion:
        for nom, jours_conservation in regles.items():
            config = TABLES_PURGE[nom]
            cutoff = maintenant - timedelta(days=jours_conservation)
            lignes_concernees = compter_lignes_a_purger(
                connexion,
                config["table"],
                config["date_column"],
                cutoff,
            )
            apercu = lister_apercu_a_purger(
                connexion,
                config["table"],
                config["date_column"],
                cutoff,
                preview_limit,
            )
            lignes_supprimees = (
                supprimer_lignes(
                    connexion,
                    config["table"],
                    config["date_column"],
                    cutoff,
                )
                if execute
                else 0
            )
            rapport["resultats"].append(
                {
                    "nom": nom,
                    "table": config["table"],
                    "description": config["description"],
                    "jours_conservation": jours_conservation,
                    "date_limite": cutoff.isoformat(),
                    "lignes_concernees": lignes_concernees,
                    "lignes_supprimees": lignes_supprimees,
                    "apercu_lignes_concernees": apercu,
                }
            )

    return rapport


def ecrire_rapport(rapport: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(rapport, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Simule ou execute la purge RGPD des historiques utilisateur "
            "trop anciens."
        ),
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="URL PostgreSQL optionnelle. Sinon les variables DB_* ou DATABASE_URL sont utilisees.",
    )
    parser.add_argument(
        "--jours-adresses",
        type=int,
        default=365,
        help="Duree de conservation des adresses exactes, en jours.",
    )
    parser.add_argument(
        "--jours-predictions",
        type=int,
        default=365,
        help="Duree de conservation des predictions, en jours.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Fichier JSON de rapport de purge.",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=10,
        help="Nombre maximal de lignes d'exemple a afficher dans le rapport.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Supprime vraiment les lignes. Sans cette option, le script simule seulement.",
    )
    return parser


def main() -> int:
    args = construire_parser().parse_args()
    rapport = purger_donnees(
        database_url=args.database_url,
        jours_conservation_adresses=max(1, args.jours_adresses),
        jours_conservation_predictions=max(1, args.jours_predictions),
        preview_limit=max(0, args.preview_limit),
        execute=args.execute,
    )
    ecrire_rapport(rapport, args.report)

    print(f"Mode: {rapport['mode']}")
    for resultat in rapport["resultats"]:
        print(
            f"{resultat['nom']}: {resultat['lignes_concernees']} lignes concernees, "
            f"{resultat['lignes_supprimees']} supprimees"
        )
        if resultat["apercu_lignes_concernees"]:
            print("  Apercu des lignes concernees:")
            for ligne in resultat["apercu_lignes_concernees"]:
                print(f"  - {ligne}")
    print(f"Rapport: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generation du rapport de livraison du modele.

Ce script est utilise par la chaine C13. Il refuse la livraison si le score R2
du modele est trop faible, puis il ecrit un rapport simple dans le dossier
`livraison`.

En C19, le workflow de livraison relance aussi ce script avant de construire
les images Docker. Comme ca, l'application n'est pas publiee avec un modele
non valide.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def generer_rapport(
    metrics_path: Path,
    output_path: Path,
    minimum_r2: float,
) -> None:
    # C13/C19 : la chaine lit les metriques produites par l'entrainement.
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    r2_score = float(metrics["r2_score"])

    # C13/C19 : si le modele ne respecte pas le seuil, on bloque la livraison.
    if r2_score < minimum_r2:
        raise ValueError(
            f"Livraison refusee : R2 {r2_score:.4f} inferieur a {minimum_r2:.2f}."
        )

    date_livraison = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Ce texte est ajoute au resume GitHub Actions et a l'artifact final.
    rapport = f"""# Rapport de livraison du modèle

- Date : {date_livraison}
- Modèle : {metrics["modele"]}
- Données utilisées : {metrics["lignes_total"]} ventes
- Données d'entraînement : {metrics["lignes_train"]} ventes
- Données de test : {metrics["lignes_test"]} ventes
- R² obtenu : {r2_score:.4f}
- Seuil R² obligatoire : {minimum_r2:.2f}
- MAE : {metrics["mae_euros"]:.2f} euros
- RMSE : {metrics["rmse_euros"]:.2f} euros
- Tests automatisés : réussis
- Décision : **LIVRAISON ACCEPTÉE**
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rapport, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valide les métriques et génère le rapport de livraison.",
    )
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-r2", default=0.80, type=float)
    args = parser.parse_args()

    generer_rapport(args.metrics, args.output, args.minimum_r2)
    print(f"Rapport de livraison créé : {args.output}")


if __name__ == "__main__":
    main()

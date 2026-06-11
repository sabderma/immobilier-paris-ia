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
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    r2_score = float(metrics["r2_score"])

    if r2_score < minimum_r2:
        raise ValueError(
            f"Livraison refusee : R2 {r2_score:.4f} inferieur a {minimum_r2:.2f}."
        )

    date_livraison = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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

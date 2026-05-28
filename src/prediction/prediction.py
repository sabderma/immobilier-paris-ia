import argparse
from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = Path("models/xgboost_prix_dvf.joblib")


def charger_modele(model_path=MODEL_PATH):
    return joblib.load(model_path)


def preparer_donnees_prediction(surface, nombre_pieces, arrondissement):
    return pd.DataFrame(
        [
            {
                "surface_reelle_bati": surface,
                "nombre_pieces_principales": nombre_pieces,
                "arrondissement": str(arrondissement),
            }
        ]
    )


def predire_prix_avec_modele(modele, surface, nombre_pieces, arrondissement):
    donnees = preparer_donnees_prediction(surface, nombre_pieces, arrondissement)
    return float(modele.predict(donnees)[0])


def predire_prix(surface, nombre_pieces, arrondissement, model_path=MODEL_PATH):
    modele = charger_modele(model_path)
    return predire_prix_avec_modele(modele, surface, nombre_pieces, arrondissement)


def main():
    parser = argparse.ArgumentParser(
        description="Predire un prix avec le modele XGBoost DVF.",
    )
    parser.add_argument("--model", default=MODEL_PATH, type=Path)
    parser.add_argument("--surface", required=True, type=float)
    parser.add_argument("--nombre-pieces", required=True, type=int)
    parser.add_argument("--arrondissement", required=True, type=int)
    args = parser.parse_args()

    prix = predire_prix(
        surface=args.surface,
        nombre_pieces=args.nombre_pieces,
        arrondissement=args.arrondissement,
        model_path=args.model,
    )

    print(f"Prix estime : {prix:,.0f} euros".replace(",", " "))


if __name__ == "__main__":
    main()

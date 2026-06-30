"""Prediction locale avec le modele XGBoost sauvegarde.

Ce fichier sert surtout a tester le modele retenu sans passer par l'API. Il
charge le modele `.joblib`, prepare les donnees comme pendant l'entrainement et
retourne un prix estime.

Pour C12, les tests verifient que ce fichier retourne bien un prix positif.
En C13, ces memes tests sont relances par GitHub Actions avant livraison.
"""

import argparse
from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = Path("models/xgboost_prix_dvf.joblib")


def charger_modele(model_path=MODEL_PATH):
    """Recharge le modele entraine depuis le dossier `models`."""
    # C12 : le test verifie que le modele sauvegarde peut encore etre recharge.
    return joblib.load(model_path)


def preparer_donnees_prediction(surface, nombre_pieces, arrondissement):
    """Met les valeurs utilisateur dans le meme format que l'entrainement."""
    # Les noms de colonnes doivent rester identiques a ceux de l'entrainement.
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
    """Lance la prediction avec un modele deja charge en memoire."""
    donnees = preparer_donnees_prediction(surface, nombre_pieces, arrondissement)
    # Le resultat doit etre un nombre positif dans les tests C12.
    return float(modele.predict(donnees)[0])


def predire_prix(surface, nombre_pieces, arrondissement, model_path=MODEL_PATH):
    """Charge le modele puis retourne le prix estime."""
    modele = charger_modele(model_path)
    return predire_prix_avec_modele(modele, surface, nombre_pieces, arrondissement)


def main():
    """Permet de tester une prediction depuis le terminal."""
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

"""Entrainement du modele XGBoost retenu apres le benchmark C7.

Ce fichier sert a creer le modele final utilise par l'application. Le benchmark
a choisi XGBoost, donc ici on l'entraine puis on sauvegarde le modele et ses
metriques.

Pour C12, ce fichier est verifie par les tests automatises du modele.
Pour C13, GitHub Actions lance aussi ce fichier pour produire un nouveau modele.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


INPUT_CSV = Path("data/final/dvf_paris_clean_2021_2025.csv")
OUTPUT_MODEL = Path("models/xgboost_prix_dvf.joblib")
OUTPUT_METRICS = Path("models/xgboost_prix_dvf_metrics.json")

FEATURES_NUMERIQUES = [
    "surface_reelle_bati",
    "nombre_pieces_principales",
]
FEATURES_CATEGORIELLES = ["arrondissement"]
FEATURES = FEATURES_NUMERIQUES + FEATURES_CATEGORIELLES
TARGET = "valeur_fonciere"


def charger_donnees(input_csv=INPUT_CSV):
    """Charge les donnees DVF et supprime les lignes qui faussent le modele."""
    df = pd.read_csv(input_csv, low_memory=False)
    df.columns = df.columns.str.lower().str.strip()

    # C12 : seules les colonnes utiles au modele sont gardees pour le test.
    colonnes = FEATURES + [TARGET]
    df = df[colonnes].copy()

    for colonne in colonnes:
        df[colonne] = pd.to_numeric(df[colonne], errors="coerce")

    df = df.dropna()
    # Les valeurs impossibles sont retirees avant l'entrainement.
    df = df[
        (df["surface_reelle_bati"] > 0)
        & (df["nombre_pieces_principales"] > 0)
        & (df["arrondissement"].between(1, 20))
        & (df[TARGET] > 0)
    ].copy()

    df["arrondissement"] = df["arrondissement"].astype(int).astype(str)
    df["nombre_pieces_principales"] = df["nombre_pieces_principales"].astype(int)

    return df[FEATURES], df[TARGET]


def construire_modele():
    """Construit le pipeline complet : preparation des colonnes + XGBoost."""
    preprocesseur = ColumnTransformer(
        transformers=[
            ("numerique", "passthrough", FEATURES_NUMERIQUES),
            (
                "arrondissement",
                OneHotEncoder(handle_unknown="ignore"),
                FEATURES_CATEGORIELLES,
            ),
        ]
    )

    # XGBoost est garde car il a gagne le benchmark contre Random Forest.
    modele = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preparation", preprocesseur),
            ("modele", modele),
        ]
    )


def entrainer_xgboost(
    input_csv=INPUT_CSV,
    output_model=OUTPUT_MODEL,
    output_metrics=OUTPUT_METRICS,
    test_size=0.2,
    random_state=42,
):
    """Entraine XGBoost, calcule les metriques et sauvegarde les fichiers."""
    # C13 : dans GitHub Actions, cette fonction recree le modele livre.
    x, y = charger_donnees(input_csv)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    pipeline = construire_modele()
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)

    # C12 : ces metriques servent de controle automatique de qualite.
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    metrics = {
        "modele": "XGBRegressor",
        "type_probleme": "regression",
        "cible": TARGET,
        "features": FEATURES,
        "lignes_total": int(len(x)),
        "lignes_train": int(len(x_train)),
        "lignes_test": int(len(x_test)),
        "r2_score": round(float(r2), 4),
        "mae_euros": round(float(mae), 2),
        "rmse_euros": round(float(mse**0.5), 2),
        "test_size": test_size,
        "random_state": random_state,
    }

    output_model = Path(output_model)
    output_model.parent.mkdir(parents=True, exist_ok=True)
    # Le fichier .joblib est ensuite recharge dans les tests C12 et livre en C13.
    joblib.dump(pipeline, output_model)

    output_metrics = Path(output_metrics)
    output_metrics.parent.mkdir(parents=True, exist_ok=True)
    output_metrics.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return pipeline, metrics


def predire_prix(modele, surface, nombre_pieces, arrondissement):
    """Teste rapidement une prediction avec le modele deja entraine."""
    # Meme format que les donnees d'entrainement, sinon le modele refuse.
    donnees = pd.DataFrame(
        [
            {
                "surface_reelle_bati": surface,
                "nombre_pieces_principales": nombre_pieces,
                "arrondissement": str(arrondissement),
            }
        ]
    )
    return float(modele.predict(donnees)[0])


def main():
    """Permet de lancer l'entrainement depuis le terminal."""
    parser = argparse.ArgumentParser(
        description="Entraine un XGBoost pour predire directement le prix DVF.",
    )
    parser.add_argument("--input", default=INPUT_CSV, type=Path)
    parser.add_argument("--output-model", default=OUTPUT_MODEL, type=Path)
    parser.add_argument("--output-metrics", default=OUTPUT_METRICS, type=Path)
    parser.add_argument("--test-size", default=0.2, type=float)
    parser.add_argument("--surface", type=float)
    parser.add_argument("--nombre-pieces", type=int)
    parser.add_argument("--arrondissement", type=int)
    args = parser.parse_args()

    modele, metrics = entrainer_xgboost(
        input_csv=args.input,
        output_model=args.output_model,
        output_metrics=args.output_metrics,
        test_size=args.test_size,
    )

    print("Modele XGBoost entraine")
    print(f"Modele sauvegarde : {args.output_model}")
    print(f"Metrics sauvegardees : {args.output_metrics}")
    print(f"Score R2 : {metrics['r2_score']}")
    print(f"MAE : {metrics['mae_euros']} euros")
    print(f"RMSE : {metrics['rmse_euros']} euros")

    if (
        args.surface is not None
        and args.nombre_pieces is not None
        and args.arrondissement is not None
    ):
        prix = predire_prix(
            modele,
            surface=args.surface,
            nombre_pieces=args.nombre_pieces,
            arrondissement=args.arrondissement,
        )
        print(f"Prix estime : {prix:,.0f} euros".replace(",", " "))


if __name__ == "__main__":
    main()

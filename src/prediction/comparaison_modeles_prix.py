import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


INPUT_CSV = Path("data/final/dvf_paris_clean_2021_2025.csv")
OUTPUT_JSON = Path("models/comparaison_xgboost_random_forest_prix.json")
OUTPUT_CSV = Path("models/comparaison_xgboost_random_forest_prix.csv")

FEATURES_NUMERIQUES = ["surface_reelle_bati", "nombre_pieces_principales"]
FEATURES_CATEGORIELLES = ["arrondissement"]
FEATURES = FEATURES_NUMERIQUES + FEATURES_CATEGORIELLES
TARGET = "valeur_fonciere"


def charger_donnees(input_csv=INPUT_CSV):
    df = pd.read_csv(input_csv, low_memory=False)
    df.columns = df.columns.str.lower().str.strip()

    df = df[FEATURES + [TARGET]].copy()

    for colonne in FEATURES + [TARGET]:
        df[colonne] = pd.to_numeric(df[colonne], errors="coerce")

    df = df.dropna()
    df = df[
        (df["surface_reelle_bati"] > 0)
        & (df["nombre_pieces_principales"] > 0)
        & (df["arrondissement"].between(1, 20))
        & (df[TARGET] > 0)
    ].copy()

    df["arrondissement"] = df["arrondissement"].astype(int).astype(str)
    df["nombre_pieces_principales"] = df["nombre_pieces_principales"].astype(int)

    return df[FEATURES], df[TARGET]


def creer_preprocesseur():
    return ColumnTransformer(
        transformers=[
            ("numerique", "passthrough", FEATURES_NUMERIQUES),
            (
                "arrondissement",
                OneHotEncoder(handle_unknown="ignore"),
                FEATURES_CATEGORIELLES,
            ),
        ]
    )


def creer_modeles(random_state=42):
    return {
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=200,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
        ),
        "XGBRegressor": XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=random_state,
            n_jobs=-1,
        ),
    }


def evaluer_modele(modele, x_train, x_test, y_train, y_test):
    pipeline = Pipeline(
        steps=[
            ("preparation", creer_preprocesseur()),
            ("modele", modele),
        ]
    )
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    return {
        "r2_score": round(float(r2), 4),
        "mae_euros": round(float(mae), 2),
        "rmse_euros": round(float(mse**0.5), 2),
    }


def comparer_modeles(
    input_csv=INPUT_CSV,
    output_json=OUTPUT_JSON,
    output_csv=OUTPUT_CSV,
    test_size=0.2,
    random_state=42,
):
    x, y = charger_donnees(input_csv)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    resultats = []
    for nom_modele, modele in creer_modeles(random_state).items():
        metrics = evaluer_modele(modele, x_train, x_test, y_train, y_test)
        resultats.append(
            {
                "modele": nom_modele,
                "cible": TARGET,
                "features": ", ".join(FEATURES),
                "lignes_total": len(x),
                "lignes_train": len(x_train),
                "lignes_test": len(x_test),
                **metrics,
            }
        )

    df_resultats = pd.DataFrame(resultats).sort_values(
        by=["rmse_euros", "mae_euros"],
    )
    meilleur_modele = df_resultats.iloc[0].to_dict()

    output_json = Path(output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(
            {
                "meilleur_modele": meilleur_modele["modele"],
                "critere": "RMSE le plus faible",
                "resultats": resultats,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_resultats.to_csv(output_csv, index=False)

    return df_resultats


def main():
    parser = argparse.ArgumentParser(
        description="Compare RandomForestRegressor et XGBRegressor sur le prix DVF.",
    )
    parser.add_argument("--input", default=INPUT_CSV, type=Path)
    parser.add_argument("--output-json", default=OUTPUT_JSON, type=Path)
    parser.add_argument("--output-csv", default=OUTPUT_CSV, type=Path)
    parser.add_argument("--test-size", default=0.2, type=float)
    parser.add_argument("--random-state", default=42, type=int)
    args = parser.parse_args()

    resultats = comparer_modeles(
        input_csv=args.input,
        output_json=args.output_json,
        output_csv=args.output_csv,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    print("Comparaison terminee")
    print(f"JSON : {args.output_json}")
    print(f"CSV : {args.output_csv}")
    print(resultats)


if __name__ == "__main__":
    main()

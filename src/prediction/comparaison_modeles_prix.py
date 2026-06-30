"""Benchmark C7 pour comparer Random Forest et XGBoost.

Ce script sert a ne pas choisir le modele au hasard. Il entraine les deux
modeles sur les memes donnees DVF, calcule les memes metriques, puis sauvegarde
les resultats pour justifier le choix final.
"""

import argparse
import json
from contextlib import nullcontext
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
MLFLOW_EXPERIMENT = "immobilier_paris_comparaison_modeles_prix"

FEATURES_NUMERIQUES = ["surface_reelle_bati", "nombre_pieces_principales"]
FEATURES_CATEGORIELLES = ["arrondissement"]
FEATURES = FEATURES_NUMERIQUES + FEATURES_CATEGORIELLES
TARGET = "valeur_fonciere"


def charger_donnees(input_csv=INPUT_CSV):
    """Charge les donnees DVF et garde seulement les lignes utilisables."""
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
    """Prepare les colonnes avant de les donner au modele."""
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


def charger_mlflow():
    """Charge MLflow si la bibliotheque est disponible dans l'environnement."""
    try:
        import mlflow
        import mlflow.sklearn  # noqa: F401
    except ImportError:
        return None

    return mlflow


def configurer_mlflow(experiment_name=MLFLOW_EXPERIMENT, tracking_uri=None):
    """Prepare MLflow pour suivre les essais, mais seulement si possible."""
    mlflow = charger_mlflow()

    if mlflow is None:
        print("MLflow n'est pas installe : comparaison lancee sans suivi MLflow.")
        return None

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    mlflow.set_experiment(experiment_name)
    return mlflow


def creer_modeles(random_state=42):
    """Cree les deux modeles candidats du benchmark C7."""
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


def entrainer_et_evaluer_modele(modele, x_train, x_test, y_train, y_test):
    """Entraine un modele et retourne ses scores sur les donnees de test."""
    pipeline = Pipeline(
        steps=[
            ("preparation", creer_preprocesseur()),
            ("modele", modele),
        ]
    )
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    # Les trois metriques permettent de comparer les modeles de facon simple.
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    metrics = {
        "r2_score": round(float(r2), 4),
        "mae_euros": round(float(mae), 2),
        "rmse_euros": round(float(mse**0.5), 2),
    }

    return pipeline, metrics


def evaluer_modele(modele, x_train, x_test, y_train, y_test):
    """Retourne seulement les metriques, utile pour les tests rapides."""
    _, metrics = entrainer_et_evaluer_modele(modele, x_train, x_test, y_train, y_test)
    return metrics


def nettoyer_parametres_mlflow(modele):
    """Transforme les parametres du modele pour les envoyer proprement a MLflow."""
    return {
        f"param_{cle}": str(valeur)
        for cle, valeur in modele.get_params(deep=False).items()
        if valeur is not None
    }


def enregistrer_essai_mlflow(
    mlflow,
    nom_modele,
    modele,
    pipeline,
    metrics,
    x_test,
    lignes_total,
    lignes_train,
    lignes_test,
):
    """Sauvegarde un essai dans MLflow pour garder une trace du benchmark."""
    with mlflow.start_run(run_name=nom_modele, nested=True):
        mlflow.set_tags(
            {
                "modele": nom_modele,
                "type_probleme": "regression",
                "cible": TARGET,
            }
        )
        mlflow.log_params(
            {
                "features": ", ".join(FEATURES),
                "preprocessing": "OneHotEncoder(arrondissement) + passthrough numerique",
            }
        )
        mlflow.log_params(nettoyer_parametres_mlflow(modele))
        mlflow.log_metrics(metrics)
        mlflow.log_metrics(
            {
                "lignes_total": lignes_total,
                "lignes_train": lignes_train,
                "lignes_test": lignes_test,
            }
        )

        exemple = x_test.head(5)
        signature = mlflow.models.infer_signature(exemple, pipeline.predict(exemple))

        try:
            mlflow.sklearn.log_model(
                pipeline,
                name="model",
                signature=signature,
                input_example=exemple,
                serialization_format="cloudpickle",
            )
        except TypeError:
            mlflow.sklearn.log_model(
                pipeline,
                artifact_path="model",
                signature=signature,
                input_example=exemple,
                serialization_format="cloudpickle",
            )


def comparer_modeles(
    input_csv=INPUT_CSV,
    output_json=OUTPUT_JSON,
    output_csv=OUTPUT_CSV,
    test_size=0.2,
    random_state=42,
    suivi_mlflow=True,
    mlflow_experiment=MLFLOW_EXPERIMENT,
    mlflow_tracking_uri=None,
):
    """Lance toute la comparaison et sauvegarde les resultats JSON et CSV."""
    x, y = charger_donnees(input_csv)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    resultats = []

    mlflow = (
        configurer_mlflow(mlflow_experiment, mlflow_tracking_uri)
        if suivi_mlflow
        else None
    )
    run_kwargs = {"run_name": "comparaison_xgboost_random_forest_prix"}
    if mlflow and mlflow.active_run() is not None:
        run_kwargs["nested"] = True
    contexte_mlflow = mlflow.start_run(**run_kwargs) if mlflow else nullcontext()

    with contexte_mlflow:
        if mlflow:
            mlflow.set_tags(
                {
                    "type_probleme": "regression",
                    "cible": TARGET,
                    "comparaison": "RandomForestRegressor vs XGBRegressor",
                }
            )
            mlflow.log_params(
                {
                    "input_csv": str(input_csv),
                    "features": ", ".join(FEATURES),
                    "test_size": test_size,
                    "random_state": random_state,
                }
            )

        for nom_modele, modele in creer_modeles(random_state).items():
            pipeline, metrics = entrainer_et_evaluer_modele(
                modele,
                x_train,
                x_test,
                y_train,
                y_test,
            )
            resultat = {
                "modele": nom_modele,
                "cible": TARGET,
                "features": ", ".join(FEATURES),
                "lignes_total": len(x),
                "lignes_train": len(x_train),
                "lignes_test": len(x_test),
                **metrics,
            }
            resultats.append(resultat)

            if mlflow:
                enregistrer_essai_mlflow(
                    mlflow,
                    nom_modele,
                    modele,
                    pipeline,
                    metrics,
                    x_test,
                    len(x),
                    len(x_train),
                    len(x_test),
                )

        df_resultats = pd.DataFrame(resultats).sort_values(
            by=["rmse_euros", "mae_euros"],
        )
        # Le modele retenu est celui qui fait le moins de grosses erreurs.
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

        if mlflow:
            mlflow.log_param("meilleur_modele", meilleur_modele["modele"])
            mlflow.log_metric("meilleur_rmse_euros", meilleur_modele["rmse_euros"])
            mlflow.log_metric("meilleur_mae_euros", meilleur_modele["mae_euros"])
            mlflow.log_metric("meilleur_r2_score", meilleur_modele["r2_score"])
            mlflow.log_artifact(str(output_json))
            mlflow.log_artifact(str(output_csv))

    return df_resultats


def main():
    """Point d'entree pour lancer le benchmark depuis le terminal."""
    parser = argparse.ArgumentParser(
        description="Compare RandomForestRegressor et XGBRegressor sur le prix DVF.",
    )
    parser.add_argument("--input", default=INPUT_CSV, type=Path)
    parser.add_argument("--output-json", default=OUTPUT_JSON, type=Path)
    parser.add_argument("--output-csv", default=OUTPUT_CSV, type=Path)
    parser.add_argument("--test-size", default=0.2, type=float)
    parser.add_argument("--random-state", default=42, type=int)
    parser.add_argument("--mlflow-experiment", default=MLFLOW_EXPERIMENT)
    parser.add_argument("--mlflow-tracking-uri")
    parser.add_argument("--sans-mlflow", action="store_true")
    args = parser.parse_args()

    resultats = comparer_modeles(
        input_csv=args.input,
        output_json=args.output_json,
        output_csv=args.output_csv,
        test_size=args.test_size,
        random_state=args.random_state,
        suivi_mlflow=not args.sans_mlflow,
        mlflow_experiment=args.mlflow_experiment,
        mlflow_tracking_uri=args.mlflow_tracking_uri,
    )

    print("Comparaison terminee")
    print(f"JSON : {args.output_json}")
    print(f"CSV : {args.output_csv}")
    print(resultats)


if __name__ == "__main__":
    main()

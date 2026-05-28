import argparse
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder


INPUT_CSV = Path("data/final/dvf_paris_clean_2021_2025.csv")
OUTPUT_CSV = Path("data/processed/dvf_paris_prediction_encode_normalise.csv")

COLONNES_NUMERIQUES = [
    "valeur_fonciere",
    "prix_m2",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "annee_vente",
    "longitude",
    "latitude",
]

COLONNES_CATEGORIELLES = [
    "arrondissement",

]


def preparer_csv_dvf(input_csv=INPUT_CSV, output_csv=OUTPUT_CSV):
    df = pd.read_csv(input_csv, low_memory=False)
    df.columns = df.columns.str.lower().str.strip()

    
       

    colonnes_utiles = COLONNES_NUMERIQUES + COLONNES_CATEGORIELLES
    df = df[colonnes_utiles].copy()

    for colonne in COLONNES_NUMERIQUES + COLONNES_CATEGORIELLES:
        df[colonne] = pd.to_numeric(df[colonne], errors="coerce")

    df = df.dropna()
    df[COLONNES_CATEGORIELLES] = df[COLONNES_CATEGORIELLES].astype(int)

    scaler = MinMaxScaler()
    donnees_normalisees = scaler.fit_transform(df[COLONNES_NUMERIQUES])
    df_numerique = pd.DataFrame(
        donnees_normalisees,
        columns=[f"{colonne}_norm" for colonne in COLONNES_NUMERIQUES],
        index=df.index,
    )

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=int)
    donnees_encodees = encoder.fit_transform(df[COLONNES_CATEGORIELLES])
    df_categories = pd.DataFrame(
        donnees_encodees,
        columns=encoder.get_feature_names_out(COLONNES_CATEGORIELLES),
        index=df.index,
    )

    df_prepare = pd.concat([df_numerique, df_categories], axis=1)

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_prepare.to_csv(output_csv, index=False)

    return df_prepare


def main():
    parser = argparse.ArgumentParser(
        description="Encode et normalise le CSV DVF pour la prediction.",
    )
    parser.add_argument("--input", default=INPUT_CSV, type=Path)
    parser.add_argument("--output", default=OUTPUT_CSV, type=Path)
    args = parser.parse_args()

    df_prepare = preparer_csv_dvf(args.input, args.output)

    print(f"CSV prepare : {args.output}")
    print(f"Lignes : {len(df_prepare)}")
    print(f"Colonnes : {len(df_prepare.columns)}")


if __name__ == "__main__":
    main()

import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw/DVF")

annees = [2021, 2022, 2023, 2024, 2025]

valeurs_problematiques = [
    "non disponible",
    "non renseigne",
    "non renseigné",
    "n/a",
    "na",
    "null",
    "none",
    ""
]

print("\n========== ANALYSE DES FICHIERS DVF AVANT NETTOYAGE ==========\n")

for annee in annees:
    fichier = RAW_DIR / f"75-{annee}.csv"

    print("\n" + "=" * 70)
    print(f"ANALYSE DU FICHIER : {fichier}")
    print("=" * 70)

    df = pd.read_csv(fichier, low_memory=False)

    df.columns = df.columns.str.lower().str.strip()

    print("\n========== INFORMATIONS GÉNÉRALES ==========\n")
    print("Nombre de lignes :", df.shape[0])
    print("Nombre de colonnes :", df.shape[1])

    print("\nColonnes du fichier :")
    print(df.columns.tolist())

    print("\n========== TYPES DES COLONNES ==========\n")
    print(df.dtypes)

    print("\n========== VALEURS MANQUANTES ==========\n")
    print(df.isnull().sum())

    print("\n========== VALEURS PROBLÉMATIQUES ==========\n")
    for colonne in df.columns:
        total = (
            df[colonne]
            .astype(str)
            .str.lower()
            .str.strip()
            .isin(valeurs_problematiques)
            .sum()
        )

        if total > 0:
            print(f"{colonne} : {total}")

    print("\n========== DOUBLONS ==========\n")
    print("Nombre de lignes dupliquées :", df.duplicated().sum())

    print("\n========== ANALYSE DVF IMPORTANTE ==========\n")

    if "code_departement" in df.columns:
        df["code_departement"] = df["code_departement"].astype(str)
        nb_paris = df[df["code_departement"] == "75"].shape[0]
        print("Nombre de lignes pour Paris :", nb_paris)

    if "nature_mutation" in df.columns:
        print("\nRépartition des natures de mutation :")
        print(df["nature_mutation"].value_counts(dropna=False))

    if "type_local" in df.columns:
        print("\nRépartition des types de locaux :")
        print(df["type_local"].value_counts(dropna=False))

    if "surface_reelle_bati" in df.columns:
        surface = pd.to_numeric(df["surface_reelle_bati"], errors="coerce")

        print("\nAnalyse surface bâtie :")
        print("Surfaces nulles ou 0 :", ((surface.isna()) | (surface == 0)).sum())
        print("Surfaces > 0 :", (surface > 0).sum())
        print("Surface minimale :", surface.min())
        print("Surface maximale :", surface.max())

    if "valeur_fonciere" in df.columns:
        prix = pd.to_numeric(df["valeur_fonciere"], errors="coerce")

        print("\nAnalyse valeur foncière :")
        print("Prix nuls ou 0 :", ((prix.isna()) | (prix == 0)).sum())
        print("Prix > 0 :", (prix > 0).sum())
        print("Prix minimum :", prix.min())
        print("Prix maximum :", prix.max())
        print("Prix moyen :", prix.mean())

    if "code_postal" in df.columns:
        print("\nRépartition par code postal :")
        print(df["code_postal"].value_counts(dropna=False).head(20))

    print("\n========== APERÇU DES DONNÉES ==========\n")
    print(df.head())

    print("\n========== STATISTIQUES ==========\n")
    print(df.describe(include="all"))

print("\n========== ANALYSE TERMINÉE ==========\n")
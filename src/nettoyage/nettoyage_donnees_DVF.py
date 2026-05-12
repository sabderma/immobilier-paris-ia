import pandas as pd
from pathlib import Path

# Dossiers
RAW_DIR = Path("data/raw/DVF")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Années à nettoyer
annees = [2025, 2024, 2023, 2022, 2021]

# Stocker tous les fichiers nettoyés
dfs_clean = []

for annee in annees:
    fichier = RAW_DIR / f"75-{annee}.csv"

    print(f"\nNettoyage du fichier : {fichier}")

    df = pd.read_csv(fichier, low_memory=False)

    # Normaliser les noms de colonnes
    df.columns = df.columns.str.lower().str.strip()

    # Garder seulement Paris
    df["code_departement"] = df["code_departement"].astype(str)
    df = df[df["code_departement"] == "75"]

    # Garder seulement les ventes d'appartements
    df = df[
        (df["nature_mutation"] == "Vente") &
        (df["type_local"] == "Appartement")
    ]

    # Convertir les colonnes numériques
    colonnes_num = [
        "valeur_fonciere",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "longitude",
        "latitude"
    ]

    for col in colonnes_num:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Supprimer les lignes inutilisables
    df = df.dropna(subset=[
        "valeur_fonciere",
        "surface_reelle_bati",
        "longitude",
        "latitude"
    ])

    df = df[
        (df["valeur_fonciere"] > 0) &
        (df["surface_reelle_bati"] > 0) &
        (df["nombre_pieces_principales"] > 0)
    ]

    # Supprimer les valeurs absurdes
    df = df[
        (df["surface_reelle_bati"] >= 9) &
        (df["surface_reelle_bati"] <= 300) &
        (df["valeur_fonciere"] >= 50000) &
        (df["valeur_fonciere"] <= 5000000)
    ]

    # Créer les colonnes utiles
    df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")
    df["annee_vente"] = df["date_mutation"].dt.year
    df["mois_vente"] = df["date_mutation"].dt.month

    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    # Corriger code postal
    df["code_postal"] = pd.to_numeric(df["code_postal"], errors="coerce")
    df = df.dropna(subset=["code_postal"])
    df["code_postal"] = df["code_postal"].astype(int).astype(str)

    # Garder seulement les codes postaux de Paris
    df = df[df["code_postal"].str.startswith("75")]

    # Créer arrondissement
    df["arrondissement"] = df["code_postal"].str[-2:].astype(int)

    # Supprimer les prix/m² absurdes
    df = df[
        (df["prix_m2"] >= 3000) &
        (df["prix_m2"] <= 25000)
    ]

    # Colonnes finales
    colonnes_finales = [
        "id_mutation",
        "date_mutation",
        "annee_vente",
        "mois_vente",
        "valeur_fonciere",
        "prix_m2",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "type_local",
        "code_postal",
        "arrondissement",
        "nom_commune",
        "adresse_nom_voie",
        "longitude",
        "latitude"
    ]

    df_final = df[colonnes_finales].drop_duplicates()

    # Sauvegarde fichier par année
    fichier_sortie = OUTPUT_DIR / f"dvf_paris_clean_{annee}.csv"
    df_final.to_csv(fichier_sortie, index=False)

    print(f"Fichier nettoyé sauvegardé : {fichier_sortie}")
    print(f"Nombre de lignes propres {annee} :", len(df_final))

    dfs_clean.append(df_final)

# Fusionner les 5 années dans un seul fichier
df_all = pd.concat(dfs_clean, ignore_index=True)
df_all = df_all.drop_duplicates()

fichier_global = "data/final/dvf_paris_clean_2021_2025.csv"
df_all.to_csv(fichier_global, index=False)

print("\nNettoyage terminé pour toutes les années")
print("Fichier global sauvegardé :", fichier_global)
print("Nombre total de lignes propres :", len(df_all))
print(df_all.head())
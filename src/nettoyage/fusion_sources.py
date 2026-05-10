import pandas as pd
from pathlib import Path


DOSSIER_SCRAPING = Path("data/raw/scraping")

fichiers_sources = {
    "annonces_century21_paris.csv": "century21",
    "annonces_laforet_paris_complet.csv": "laforet",
    "annonces_lefigaro_paris.csv": "lefigaro",
    "annonces_orpi_paris.csv": "orpi",
    "annonces_plaza_paris.csv": "plaza",
}

dataframes = []

for fichier, source in fichiers_sources.items():
    chemin = DOSSIER_SCRAPING / fichier

    df = pd.read_csv(chemin)

    # Ajouter la colonne source
    df["source"] = source

    dataframes.append(df)

# Fusionner tous les CSV
df_final = pd.concat(dataframes, ignore_index=True)



# Sauvegarde finale
chemin_sortie = Path("data/processed/annonces_scraping_fusionnees.csv")


df_final.to_csv(chemin_sortie, index=False, encoding="utf-8-sig")

print("Fusion terminée")
print(f"Fichier créé : {chemin_sortie}")
print(f"Nombre total de lignes : {len(df_final)}")
print(df_final.head())
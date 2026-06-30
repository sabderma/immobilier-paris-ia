"""Fusion des fichiers bruts de scraping immobilier.

Ce script correspond au debut de la C3 pour le scraping : il prend les CSV de
chaque site, ajoute la source, puis cree un fichier fusionne pour la suite du
nettoyage.
"""

import pandas as pd
from pathlib import Path


DOSSIER_SCRAPING = Path("data/raw/scraping")

# Chaque fichier brut est associe au nom de sa source.
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

    # Lecture d'un fichier brut produit par un scraper C1.
    df = pd.read_csv(chemin)

    # La colonne source permet de savoir de quel site vient chaque annonce.
    df["source"] = source

    dataframes.append(df)

# Fusionne toutes les sources dans un seul tableau.
df_final = pd.concat(dataframes, ignore_index=True)



# Sauvegarde du fichier source fusionne, avant nettoyage master/golden.
chemin_sortie = Path("data/processed/annonces_scraping_fusionnees.csv")


df_final.to_csv(chemin_sortie, index=False, encoding="utf-8-sig")

print("Fusion terminée")
print(f"Fichier créé : {chemin_sortie}")
print(f"Nombre total de lignes : {len(df_final)}")
print(df_final.head())

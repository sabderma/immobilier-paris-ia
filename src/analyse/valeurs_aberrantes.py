# =========================================================
# Analyse des anomalies DVF — Z-Score + IQR
# Projet : Analyse immobilière Paris
# Auteur : Malek Silarbi
# =========================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import zscore

# =========================================================
# CONFIGURATION
# =========================================================

INPUT_FILE = "data/final/dvf_paris_clean_2021_2025.csv"

OUTPUT_FOLDER = "data/visuals/anomalies"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================================================
# CHARGEMENT DES DONNÉES
# =========================================================

print("Chargement des données DVF...")

df = pd.read_csv(INPUT_FILE)

print(f"Nombre de lignes : {len(df)}")

# =========================================================
# NETTOYAGE MINIMUM
# =========================================================

colonnes_numeriques = [
    "valeur_fonciere",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "prix_m2"
]

for col in colonnes_numeriques:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=colonnes_numeriques)

# =========================================================
# MÉTHODE 1 — Z-SCORE
# =========================================================

print("\nDétection anomalies avec Z-Score...")

zscore_cols = [
    "valeur_fonciere",
    "surface_reelle_bati",
    "prix_m2"
]

for col in zscore_cols:

    # Calcul du z-score
    df[f"{col}_zscore"] = zscore(df[col])

    # Détection anomalie
    df[f"{col}_anomalie_zscore"] = (
        np.abs(df[f"{col}_zscore"]) > 3
    )

    nb = df[f"{col}_anomalie_zscore"].sum()

    print(f"{col} : {nb} anomalies détectées")

# =========================================================
# MÉTHODE 2 — IQR
# =========================================================

print("\nDétection anomalies avec IQR...")

for col in zscore_cols:

    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)

    IQR = Q3 - Q1

    borne_basse = Q1 - 1.5 * IQR
    borne_haute = Q3 + 1.5 * IQR

    df[f"{col}_anomalie_iqr"] = (
        (df[col] < borne_basse) |
        (df[col] > borne_haute)
    )

    nb = df[f"{col}_anomalie_iqr"].sum()

    print(f"{col} : {nb} anomalies détectées")

# =========================================================
# SAUVEGARDE CSV ANOMALIES
# =========================================================

print("\nSauvegarde des anomalies...")

# Z-SCORE
df_zscore = df[
    (df["valeur_fonciere_anomalie_zscore"]) |
    (df["surface_reelle_bati_anomalie_zscore"]) |
    (df["prix_m2_anomalie_zscore"])
]

df_zscore.to_csv(
    "data/final/anomalies_zscore.csv",
    index=False
)

# IQR
df_iqr = df[
    (df["valeur_fonciere_anomalie_iqr"]) |
    (df["surface_reelle_bati_anomalie_iqr"]) |
    (df["prix_m2_anomalie_iqr"])
]

df_iqr.to_csv(
    "data/final/anomalies_iqr.csv",
    index=False
)

print("CSV anomalies sauvegardés.")

# =========================================================
# DASHBOARD — HISTOGRAMME PRIX M²
# =========================================================

print("\nCréation des visualisations...")

plt.figure(figsize=(12, 6))

plt.hist(
    df["prix_m2"],
    bins=100
)

plt.title("Distribution du prix au m²")
plt.xlabel("Prix au m²")
plt.ylabel("Nombre de biens")

plt.savefig(
    f"{OUTPUT_FOLDER}/histogramme_prix_m2.png",
    bbox_inches="tight"
)

plt.close()

# =========================================================
# BOXPLOT PRIX M²
# =========================================================

plt.figure(figsize=(10, 5))

plt.boxplot(df["prix_m2"], vert=False)

plt.title("Boxplot prix au m²")

plt.savefig(
    f"{OUTPUT_FOLDER}/boxplot_prix_m2.png",
    bbox_inches="tight"
)

plt.close()

# =========================================================
# SCATTER SURFACE VS PRIX
# =========================================================

plt.figure(figsize=(10, 6))

plt.scatter(
    df["surface_reelle_bati"],
    df["valeur_fonciere"],
    alpha=0.4
)

plt.title("Surface vs Valeur foncière")
plt.xlabel("Surface")
plt.ylabel("Valeur foncière")

plt.savefig(
    f"{OUTPUT_FOLDER}/scatter_surface_prix.png",
    bbox_inches="tight"
)

plt.close()

# =========================================================
# TOP 20 PRIX M² LES PLUS ÉLEVÉS
# =========================================================

top20 = df.sort_values(
    by="prix_m2",
    ascending=False
).head(20)

plt.figure(figsize=(14, 6))

plt.bar(
    range(len(top20)),
    top20["prix_m2"]
)

plt.title("Top 20 des prix au m² les plus élevés")
plt.xlabel("Biens")
plt.ylabel("Prix au m²")

plt.savefig(
    f"{OUTPUT_FOLDER}/top20_prix_m2.png",
    bbox_inches="tight"
)

plt.close()

# =========================================================
# RÉSUMÉ FINAL
# =========================================================

print("\n===================================")
print("Analyse des anomalies terminée")
print("===================================")

print(f"Images sauvegardées dans : {OUTPUT_FOLDER}")

print(f"Nombre anomalies Z-Score : {len(df_zscore)}")
print(f"Nombre anomalies IQR : {len(df_iqr)}")
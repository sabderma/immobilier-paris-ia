import pandas as pd

# =========================================
# CHEMIN DU CSV
# =========================================

CSV_PATH = "data/final/dvf_paris_clean_2021_2025.csv"

# =========================================
# CHARGEMENT DU CSV
# =========================================

df = pd.read_csv(CSV_PATH, low_memory=False)

print("CSV chargé avec succès")
print(f"Nombre de lignes avant suppression : {len(df)}")

# =========================================
# CONVERSION EN NUMÉRIQUE
# =========================================

colonnes_numeriques = [
    "latitude",
    "longitude",
    "surface_reelle_bati",
    "nombre_pieces_principales"
]

for col in colonnes_numeriques:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================================
# DÉTECTION DES ANOMALIES
# =========================================

anomalie_coordonnees = (
    (df["latitude"] < 48.80) |
    (df["latitude"] > 48.90) |
    (df["longitude"] < 2.20) |
    (df["longitude"] > 2.45)
)

surface_par_piece = (
    df["surface_reelle_bati"] /
    df["nombre_pieces_principales"]
)

anomalie_pieces = (
    (df["nombre_pieces_principales"] <= 0) |
    (surface_par_piece < 8) |
    (surface_par_piece > 80)
)

anomalies = (
    anomalie_coordonnees |
    anomalie_pieces
)

# =========================================
# SUPPRESSION
# =========================================

nb_anomalies = anomalies.sum()

df = df[~anomalies]

print(f"Lignes supprimées : {nb_anomalies}")
print(f"Nombre de lignes restantes : {len(df)}")

# =========================================
# ÉCRASEMENT DU CSV ORIGINAL
# =========================================

df.to_csv(CSV_PATH, index=False)

print("CSV mis à jour avec succès")
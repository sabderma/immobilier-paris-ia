import pandas as pd

# =========================================
# CHEMIN DU CSV
# =========================================

CSV_PATH = "data/final/annonces_scraping_nettoyees_golden.csv"

# =========================================
# CHARGEMENT DU CSV
# =========================================

df = pd.read_csv(
    CSV_PATH,
    sep=";",
    low_memory=False
)

print("CSV chargé avec succès")
print(f"Nombre de lignes avant suppression : {len(df)}")

# =========================================
# CONVERSION DES COLONNES NUMÉRIQUES
# =========================================

colonnes_numeriques = [
    "prix",
    "surface",
    "prix_m2",
    "nb_pieces"
]

for col in colonnes_numeriques:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# =========================================
# DÉTECTION DES ANOMALIES
# =========================================

# Prix aberrants
anomalie_prix = (
    (df["prix"] < 50000) |
    (df["prix"] > 10000000)
)

# Surface aberrante
anomalie_surface = (
    (df["surface"] < 9) |
    (df["surface"] > 500)
)

# Prix au m² aberrant
anomalie_prix_m2 = (
    (df["prix_m2"] < 2000) |
    (df["prix_m2"] > 50000)
)

# Surface par pièce
surface_par_piece = (
    df["surface"] / df["nb_pieces"]
)

# Nombre de pièces incohérent
anomalie_pieces = (
    (df["nb_pieces"] <= 0) |
    (surface_par_piece < 8) |
    (surface_par_piece > 80)
)

# =========================================
# COMBINAISON DES ANOMALIES
# =========================================

anomalies = (
    anomalie_prix |
    anomalie_surface |
    anomalie_prix_m2 |
    anomalie_pieces
)

# =========================================
# AFFICHAGE
# =========================================

print("\nAnomalies détectées :")
print(f"Prix aberrants : {anomalie_prix.sum()}")
print(f"Surfaces aberrantes : {anomalie_surface.sum()}")
print(f"Prix/m² aberrants : {anomalie_prix_m2.sum()}")
print(f"Pièces incohérentes : {anomalie_pieces.sum()}")
print(f"Total lignes supprimées : {anomalies.sum()}")

# =========================================
# SUPPRESSION
# =========================================

df = df[~anomalies]

print(f"\nNombre de lignes restantes : {len(df)}")

# =========================================
# ÉCRASEMENT DU CSV ORIGINAL
# =========================================

df.to_csv(CSV_PATH, index=False)

print("\nCSV mis à jour avec succès")
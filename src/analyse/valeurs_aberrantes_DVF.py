import os
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# =========================================
# CONFIGURATION POSTGRESQL
# =========================================

USER = "postgres"
PASSWORD = "12345"
HOST = "localhost"
PORT = "5433"
DATABASE = "immobilier_paris"

engine = create_engine(
    f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
)

# =========================================
# DOSSIER DE SORTIE DES DASHBOARDS
# =========================================

OUTPUT_DIR = "data/visuals/anomalies"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================
# CHARGEMENT DU RÉSUMÉ SQL DES ANOMALIES
# =========================================

query_resume = """
SELECT 'Nombre de pièces incohérent' AS type_anomalie, COUNT(*) AS total
FROM dvf_paris_appartements
WHERE nombre_pieces_principales <= 0
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) < 8
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) > 80

UNION ALL

SELECT 'coordonnees_hors_paris', COUNT(*)
FROM dvf_paris_appartements
WHERE latitude NOT BETWEEN 48.80 AND 48.90
   OR longitude NOT BETWEEN 2.20 AND 2.45

UNION ALL

SELECT 'prix_m2_aberrant', COUNT(*)
FROM dvf_paris_appartements
WHERE prix_m2 < 2000 OR prix_m2 > 40000

UNION ALL

SELECT 'prix_total_aberrant', COUNT(*)
FROM dvf_paris_appartements
WHERE valeur_fonciere < 50000 OR valeur_fonciere > 5000000

UNION ALL

SELECT 'surface_aberrante', COUNT(*)
FROM dvf_paris_appartements
WHERE surface_reelle_bati < 9 OR surface_reelle_bati > 300

UNION ALL

SELECT 'coordonnees_manquantes', COUNT(*)
FROM dvf_paris_appartements
WHERE latitude IS NULL OR longitude IS NULL;
"""

df_resume = pd.read_sql(query_resume, engine)

print(df_resume)

# =========================================
# DASHBOARD 1 : BARPLOT DES ANOMALIES
# =========================================

plt.figure(figsize=(11, 6))
plt.bar(df_resume["type_anomalie"], df_resume["total"])

plt.title("Nombre d'anomalies détectées dans les données DVF")
plt.xlabel("Type d'anomalie")
plt.ylabel("Nombre de lignes")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/01_nombre_anomalies_par_type.png", dpi=300)
plt.show()

# =========================================
# DASHBOARD 2 : CAMEMBERT DES ANOMALIES NON NULLES
# =========================================

df_non_nulles = df_resume[df_resume["total"] > 0]

plt.figure(figsize=(8, 8))
plt.pie(
    df_non_nulles["total"],
    labels=df_non_nulles["type_anomalie"],
    autopct="%1.1f%%",
    startangle=90
)

plt.title("Répartition des anomalies DVF détectées")
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/02_repartition_anomalies.png", dpi=300)
plt.show()

# =========================================
# CHARGEMENT DES DONNÉES DVF COMPLÈTES
# =========================================

query_dvf = """
SELECT
    id_mutation,
    valeur_fonciere,
    prix_m2,
    surface_reelle_bati,
    nombre_pieces_principales,
    arrondissement,
    latitude,
    longitude
FROM dvf_paris_appartements;
"""

df = pd.read_sql(query_dvf, engine)

# =========================================
# AJOUT DES COLONNES D'ANOMALIES
# =========================================

df["surface_par_piece"] = (
    df["surface_reelle_bati"] / df["nombre_pieces_principales"]
)

df["anomalie_pieces"] = (
    (df["nombre_pieces_principales"] <= 0) |
    (df["surface_par_piece"] < 8) |
    (df["surface_par_piece"] > 80)
)

df["anomalie_coordonnees_hors_paris"] = (
    (df["latitude"] < 48.80) |
    (df["latitude"] > 48.90) |
    (df["longitude"] < 2.20) |
    (df["longitude"] > 2.45)
)

df["est_aberrante"] = (
    df["anomalie_pieces"] |
    df["anomalie_coordonnees_hors_paris"]
)

# =========================================
# DASHBOARD 3 : SURFACE PAR PIÈCE
# =========================================

plt.figure(figsize=(10, 6))
plt.hist(df["surface_par_piece"].dropna(), bins=60)

plt.title("Distribution de la surface par pièce")
plt.xlabel("Surface par pièce en m²")
plt.ylabel("Nombre de ventes")
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/03_distribution_surface_par_piece.png", dpi=300)
plt.show()

# =========================================
# DASHBOARD 4 : ANOMALIES PAR ARRONDISSEMENT
# =========================================

anomalies_arrondissement = (
    df[df["est_aberrante"]]
    .groupby("arrondissement")
    .size()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10, 6))
plt.bar(
    anomalies_arrondissement.index.astype(str),
    anomalies_arrondissement.values
)

plt.title("Nombre d'anomalies DVF par arrondissement")
plt.xlabel("Arrondissement")
plt.ylabel("Nombre d'anomalies")
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/04_anomalies_par_arrondissement.png", dpi=300)
plt.show()

# =========================================
# DASHBOARD 5 : SURFACE VS NOMBRE DE PIÈCES
# =========================================

df_normal = df[df["est_aberrante"] == False]
df_anomalies = df[df["est_aberrante"] == True]

plt.figure(figsize=(10, 6))

plt.scatter(
    df_normal["nombre_pieces_principales"],
    df_normal["surface_reelle_bati"],
    alpha=0.4,
    label="Données normales"
)

plt.scatter(
    df_anomalies["nombre_pieces_principales"],
    df_anomalies["surface_reelle_bati"],
    alpha=0.8,
    label="Valeurs aberrantes"
)

plt.title("Surface vs nombre de pièces - détection des anomalies")
plt.xlabel("Nombre de pièces principales")
plt.ylabel("Surface réelle bâtie")
plt.legend()
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/05_surface_vs_pieces.png", dpi=300)
plt.show()

# =========================================
# EXPORT CSV DES ANOMALIES
# =========================================

df_anomalies.to_csv(
    "data/processed/anomalies_dvf.csv",
    index=False
)

print("Dashboards enregistrés dans :", OUTPUT_DIR)
print("CSV des anomalies enregistré dans : data/processed/anomalies_dvf.csv")
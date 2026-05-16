import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import os

# ================================
# CONFIGURATION POSTGRESQL
# ================================

USER = "postgres"
PASSWORD = "12345"
HOST = "localhost"
PORT = "5433"
DATABASE = "immobilier_paris"

engine = create_engine(
    f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
)

# ================================
# DOSSIER DE SORTIE
# ================================

OUTPUT_DIR = "data/visuals/comparaison_dvf_scrap"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================================
# 1. PRIX MOYEN AU M² PAR ARRONDISSEMENT
# ================================

query_arrondissement = """
WITH scraping_clean AS (
    SELECT
        CAST(SUBSTRING(localisation FROM '750([0-9]{2})') AS INTEGER) AS arrondissement,
        prix_m2
    FROM golden_data_scraping
    WHERE prix_m2 IS NOT NULL
      AND localisation IS NOT NULL
      AND localisation LIKE '%750%'
),
dvf_moyenne AS (
    SELECT
        arrondissement,
        AVG(prix_m2) AS prix_m2_dvf
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND arrondissement IS NOT NULL
    GROUP BY arrondissement
),
scraping_moyenne AS (
    SELECT
        arrondissement,
        AVG(prix_m2) AS prix_m2_scraping
    FROM scraping_clean
    WHERE arrondissement IS NOT NULL
    GROUP BY arrondissement
)
SELECT
    d.arrondissement,
    d.prix_m2_dvf,
    s.prix_m2_scraping
FROM dvf_moyenne d
JOIN scraping_moyenne s
ON d.arrondissement = s.arrondissement
ORDER BY d.arrondissement;
"""

with engine.connect() as conn:
    df_arr = pd.read_sql(text(query_arrondissement), conn)

# ================================
# GRAPHIQUE 1
# ================================

plt.figure(figsize=(14, 7))

x = range(len(df_arr))
width = 0.4

plt.bar(
    [i - width / 2 for i in x],
    df_arr["prix_m2_dvf"],
    width=width,
    label="DVF - prix réel vendu"
)

plt.bar(
    [i + width / 2 for i in x],
    df_arr["prix_m2_scraping"],
    width=width,
    label="Scraping - prix affiché"
)

plt.title("Comparaison du prix moyen au m² par arrondissement", fontsize=16)
plt.xlabel("Arrondissement")
plt.ylabel("Prix moyen au m² (€)")
plt.xticks(x, df_arr["arrondissement"])
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/comparaison_prix_m2_arrondissement.png", dpi=300)
plt.show()

# ================================
# 2. ÉCART ENTRE PRIX ANNONCÉ ET PRIX RÉEL
# ================================

df_arr["ecart_euros"] = df_arr["prix_m2_scraping"] - df_arr["prix_m2_dvf"]
df_arr["ecart_pourcentage"] = (
    df_arr["ecart_euros"] / df_arr["prix_m2_dvf"]
) * 100

df_ecart = df_arr.sort_values("ecart_pourcentage", ascending=False)

# ================================
# GRAPHIQUE 2
# ================================

plt.figure(figsize=(14, 7))

plt.bar(
    df_ecart["arrondissement"].astype(str),
    df_ecart["ecart_pourcentage"]
)

plt.axhline(0, linewidth=1)

plt.title("Écart en % entre prix affiché et prix réel par arrondissement", fontsize=16)
plt.xlabel("Arrondissement")
plt.ylabel("Écart (%)")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/ecart_prix_annonce_reel_arrondissement.png", dpi=300)
plt.show()

# ================================
# 3. COMPARAISON PAR TRANCHE DE SURFACE
# ================================

query_surface = """
WITH dvf_surface AS (
    SELECT
        CASE
            WHEN surface_reelle_bati > 0 AND surface_reelle_bati <= 20 THEN '0-20 m²'
            WHEN surface_reelle_bati > 20 AND surface_reelle_bati <= 40 THEN '20-40 m²'
            WHEN surface_reelle_bati > 40 AND surface_reelle_bati <= 60 THEN '40-60 m²'
            WHEN surface_reelle_bati > 60 AND surface_reelle_bati <= 100 THEN '60-100 m²'
            WHEN surface_reelle_bati > 100 THEN '100 m² et +'
        END AS tranche_surface,
        AVG(prix_m2) AS prix_m2_dvf
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND surface_reelle_bati IS NOT NULL
    GROUP BY tranche_surface
),
scraping_surface AS (
    SELECT
        CASE
            WHEN surface > 0 AND surface <= 20 THEN '0-20 m²'
            WHEN surface > 20 AND surface <= 40 THEN '20-40 m²'
            WHEN surface > 40 AND surface <= 60 THEN '40-60 m²'
            WHEN surface > 60 AND surface <= 100 THEN '60-100 m²'
            WHEN surface > 100 THEN '100 m² et +'
        END AS tranche_surface,
        AVG(prix_m2) AS prix_m2_scraping
    FROM golden_data_scraping
    WHERE prix_m2 IS NOT NULL
      AND surface IS NOT NULL
    GROUP BY tranche_surface
)
SELECT
    d.tranche_surface,
    d.prix_m2_dvf,
    s.prix_m2_scraping
FROM dvf_surface d
JOIN scraping_surface s
ON d.tranche_surface = s.tranche_surface
WHERE d.tranche_surface IS NOT NULL
ORDER BY
    CASE d.tranche_surface
        WHEN '0-20 m²' THEN 1
        WHEN '20-40 m²' THEN 2
        WHEN '40-60 m²' THEN 3
        WHEN '60-100 m²' THEN 4
        WHEN '100 m² et +' THEN 5
    END;
"""

with engine.connect() as conn:
    df_surface = pd.read_sql(text(query_surface), conn)

# ================================
# GRAPHIQUE 3
# ================================

plt.figure(figsize=(12, 7))

x = range(len(df_surface))
width = 0.4

plt.bar(
    [i - width / 2 for i in x],
    df_surface["prix_m2_dvf"],
    width=width,
    label="DVF - prix réel vendu"
)

plt.bar(
    [i + width / 2 for i in x],
    df_surface["prix_m2_scraping"],
    width=width,
    label="Scraping - prix affiché"
)

plt.title("Comparaison du prix moyen au m² par tranche de surface", fontsize=16)
plt.xlabel("Tranche de surface")
plt.ylabel("Prix moyen au m² (€)")
plt.xticks(x, df_surface["tranche_surface"])
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/comparaison_prix_m2_surface.png", dpi=300)
plt.show()


print("Graphiques générés avec succès !")
print(f"Dossier : {OUTPUT_DIR}")
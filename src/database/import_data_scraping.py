"""Import des donnees scraping dans PostgreSQL pour la competence C4.

Ce script prend les fichiers CSV source, master et golden, puis les ajoute dans
les tables PostgreSQL correspondantes. Il sert quand je veux importer depuis
Python au lieu de passer par Docker ou DBeaver.
"""

import pandas as pd

from db_config import construire_engine

# =========================================
# CONFIGURATION POSTGRESQL
# =========================================

engine = construire_engine()

# =========================================
# IMPORT TABLE source_data_scraping
# =========================================

df_source = pd.read_csv(
    "data/processed/annonces_scraping_fusionnees.csv"
)

# Import des annonces fusionnees dans la table source.
df_source.to_sql(
    "source_data_scraping",
    engine,
    if_exists="append",
    index=False
)

print("Import source_data_scraping terminé !")
print(f"Nombre de lignes importées : {len(df_source)}")


# =========================================
# IMPORT TABLE master_data_scraping
# =========================================

df_master = pd.read_csv(
    "data/processed/annonces_scraping_nettoyees_master.csv",
    sep=";"
)

# Import des annonces apres premier nettoyage dans la table master.
df_master.to_sql(
    "master_data_scraping",
    engine,
    if_exists="append",
    index=False
)

print("Import master_data_scraping terminé !")
print(f"Nombre de lignes importées : {len(df_master)}")





# =========================================
# IMPORT TABLE golden_data_scraping
# =========================================

df_golden = pd.read_csv(
    "data/final/annonces_scraping_nettoyees_golden.csv"
)

# Import des annonces finales propres dans la table golden.
df_golden.to_sql(
    "golden_data_scraping",
    engine,
    if_exists="append",
    index=False
)

print("Import golden_data_scraping terminé !")
print(f"Nombre de lignes importées : {len(df_golden)}")

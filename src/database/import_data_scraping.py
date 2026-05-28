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
    "data/final/annonces_scraping_nettoyees_golden.csv",
    sep=";"
)

df_golden.to_sql(
    "golden_data_scraping",
    engine,
    if_exists="append",
    index=False
)

print("Import master_data_scraping terminé !")
print(f"Nombre de lignes importées : {len(df_golden)}")

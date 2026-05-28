import pandas as pd

from db_config import construire_engine

# =========================================
# CONFIGURATION POSTGRESQL
# =========================================

engine = construire_engine()

# =========================================
# IMPORT DU FICHIER DVF NETTOYÉ
# =========================================

df_dvf = pd.read_csv(
    "data/final/dvf_paris_clean_2021_2025.csv"
)

# =========================================
# IMPORT DANS POSTGRESQL
# =========================================

df_dvf.to_sql(
    "dvf_paris_appartements",
    engine,
    if_exists="append",
    index=False
)

# =========================================
# MESSAGE FINAL
# =========================================

print("Import dvf_paris_appartements terminé !")
print(f"Nombre de lignes importées : {len(df_dvf)}")

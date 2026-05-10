import pandas as pd
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



df = pd.read_csv(
    "data/processed/annonces_scraping_fusionnees.csv"
)



df.to_sql(
    "source_data_scraping",   
    engine,
    if_exists="append",       
    index=False
)


print("Import des données terminé avec succès !")
print(f"Nombre de lignes importées : {len(df)}")
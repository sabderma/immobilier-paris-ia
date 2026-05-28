from sqlalchemy import text

from db_config import construire_engine

try:
    engine = construire_engine()

    with engine.connect() as connexion:
        result = connexion.execute(text("SELECT version();"))

        print("Connexion PostgreSQL réussie !")
        print(result.fetchone())

except Exception as e:
    print("Erreur de connexion :")
    print(e)

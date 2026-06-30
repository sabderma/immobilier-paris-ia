"""Petit test de connexion PostgreSQL.

Ce fichier sert a verifier que la base est accessible avant de lancer les
imports ou l'API.
"""

from sqlalchemy import text

from db_config import construire_engine

try:
    engine = construire_engine()

    with engine.connect() as connexion:
        # Requete simple : si elle passe, PostgreSQL repond correctement.
        result = connexion.execute(text("SELECT version();"))

        print("Connexion PostgreSQL réussie !")
        print(result.fetchone())

except Exception as e:
    print("Erreur de connexion :")
    print(e)

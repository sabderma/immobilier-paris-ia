from sqlalchemy import create_engine, text



USER = "postgres"
PASSWORD = "12345"
HOST = "localhost"
PORT = "5433"
DATABASE = "immobilier_paris"



try:
    engine = create_engine(
        f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    )

    with engine.connect() as connexion:
        result = connexion.execute(text("SELECT version();"))

        print("Connexion PostgreSQL réussie !")
        print(result.fetchone())

except Exception as e:
    print("Erreur de connexion :")
    print(e)
DROP TABLE IF EXISTS source_data_scraping;
DROP TABLE IF EXISTS master_data_scraping;
DROP TABLE IF EXISTS golden_data_scraping;
DROP TABLE IF EXISTS dvf_paris_appartements;

CREATE TABLE source_data_scraping (
    id SERIAL PRIMARY KEY,

    type TEXT,
    prix TEXT,
    surface TEXT,
    nb_pieces TEXT,
    localisation TEXT,
    details TEXT,
    source VARCHAR(100) ,
    prix_m2 TEXT,

    date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE master_data_scraping (
    id SERIAL PRIMARY KEY,

    type TEXT,
    prix TEXT,
    surface TEXT,
    nb_pieces TEXT,
    localisation TEXT,
    details TEXT,
    source VARCHAR(100) ,
    prix_m2 TEXT,

    date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);




DROP TABLE IF EXISTS golden_data_scraping;

CREATE TABLE golden_data_scraping (
    id SERIAL PRIMARY KEY,

    source VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    prix NUMERIC(12,2) NOT NULL,
    surface NUMERIC(10,2) NOT NULL,
    nb_pieces INTEGER NOT NULL,
    localisation VARCHAR(100) NOT NULL,
    prix_m2 NUMERIC(12,2) NOT NULL,
    date_scraping TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);




CREATE TABLE dvf_paris_appartements (

    id SERIAL PRIMARY KEY,

    id_mutation VARCHAR(50) NOT NULL,
    date_mutation DATE NOT NULL,

    annee_vente INTEGER NOT NULL,
    mois_vente INTEGER NOT NULL,

    valeur_fonciere NUMERIC(12,2) NOT NULL,
    prix_m2 NUMERIC(10,2) NOT NULL,

    surface_reelle_bati NUMERIC(10,2) NOT NULL,
    nombre_pieces_principales INTEGER NOT NULL,

    type_local VARCHAR(50) NOT NULL,

    code_postal VARCHAR(10) NOT NULL,
    arrondissement INTEGER NOT NULL,

    nom_commune VARCHAR(100) NOT NULL,
    adresse_nom_voie TEXT NOT NULL,

    longitude NUMERIC(10,6) NOT NULL,
    latitude NUMERIC(10,6) NOT NULL

);

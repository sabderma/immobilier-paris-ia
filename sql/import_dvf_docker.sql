-- =========================================================
-- IMPORT AUTOMATIQUE DES CSV DANS POSTGRESQL
-- =========================================================
-- Ce fichier est execute par Docker au premier demarrage de la base.
-- Il charge d'abord les CSV dans des tables temporaires, puis copie les
-- donnees dans les vraies tables du projet.
-- =========================================================

-- Table temporaire pour charger le CSV DVF avant insertion finale.
CREATE TEMP TABLE dvf_import (
    id_mutation VARCHAR(50),
    date_mutation DATE,
    annee_vente INTEGER,
    mois_vente INTEGER,
    valeur_fonciere NUMERIC,
    prix_m2 NUMERIC,
    surface_reelle_bati NUMERIC,
    nombre_pieces_principales NUMERIC,
    type_local VARCHAR(50),
    code_postal VARCHAR(10),
    arrondissement INTEGER,
    nom_commune VARCHAR(100),
    adresse_nom_voie TEXT,
    longitude NUMERIC,
    latitude NUMERIC
);

COPY dvf_import
FROM '/docker-entrypoint-initdb.d/dvf.csv'
WITH (FORMAT CSV, HEADER TRUE);

-- Insertion des DVF nettoyes dans la table finale.
INSERT INTO dvf_paris_appartements (
    id_mutation,
    date_mutation,
    annee_vente,
    mois_vente,
    valeur_fonciere,
    prix_m2,
    surface_reelle_bati,
    nombre_pieces_principales,
    type_local,
    code_postal,
    arrondissement,
    nom_commune,
    adresse_nom_voie,
    longitude,
    latitude
)
SELECT
    id_mutation,
    date_mutation,
    annee_vente,
    mois_vente,
    valeur_fonciere,
    prix_m2,
    surface_reelle_bati,
    nombre_pieces_principales::INTEGER,
    type_local,
    code_postal,
    arrondissement,
    nom_commune,
    adresse_nom_voie,
    longitude,
    latitude
FROM dvf_import;

-- Table temporaire pour charger le CSV golden scraping.
CREATE TEMP TABLE scraping_import (
    source VARCHAR(100),
    type VARCHAR(50),
    prix NUMERIC,
    surface NUMERIC,
    prix_m2 NUMERIC,
    nb_pieces INTEGER,
    localisation VARCHAR(100)
);

COPY scraping_import
FROM '/docker-entrypoint-initdb.d/scraping.csv'
WITH (FORMAT CSV, HEADER TRUE);

-- Insertion des annonces propres dans la table golden.
INSERT INTO golden_data_scraping (
    source,
    type,
    prix,
    surface,
    prix_m2,
    nb_pieces,
    localisation
)
SELECT
    source,
    type,
    prix,
    surface,
    prix_m2,
    nb_pieces,
    localisation
FROM scraping_import;

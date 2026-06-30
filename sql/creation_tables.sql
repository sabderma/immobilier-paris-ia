-- =========================================================
-- CREATION DES TABLES DU PROJET IMMOBILIER PARIS
-- =========================================================
-- Ce script prépare la base PostgreSQL du projet.
-- Il supprime les anciennes tables si elles existent déjà,
-- puis il recrée les tables utilisées pour stocker les données.
-- C'est une preuve centrale pour la competence C4 : création et stockage.
--
-- Logique des tables :
-- 1. source_data_scraping   : annonces brutes récupérées par scraping
-- 2. master_data_scraping   : annonces après un premier nettoyage
-- 3. golden_data_scraping   : annonces finales, propres et exploitables
-- 4. dvf_paris_appartements : ventes réelles DVF nettoyées
-- =========================================================


-- On supprime les tables existantes pour repartir sur une base propre.
DROP TABLE IF EXISTS source_data_scraping;
DROP TABLE IF EXISTS master_data_scraping;
DROP TABLE IF EXISTS golden_data_scraping;
DROP TABLE IF EXISTS dvf_paris_appartements;


-- =========================================================
-- TABLE 1 : source_data_scraping
-- =========================================================
-- Cette table stocke les annonces immobilières brutes.
-- Les colonnes sont en TEXT car les données viennent directement
-- des sites web et ne sont pas encore nettoyées.
CREATE TABLE source_data_scraping (
    id SERIAL PRIMARY KEY,

    -- Informations récupérées depuis les annonces.
    type TEXT,
    prix TEXT,
    surface TEXT,
    nb_pieces TEXT,
    localisation TEXT,
    details TEXT,
    source VARCHAR(100),
    prix_m2 TEXT,

    -- Date automatique de récupération ou d'import.
    date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- TABLE 2 : master_data_scraping
-- =========================================================
-- Cette table sert d'étape intermédiaire.
-- Elle garde les annonces après un premier nettoyage,
-- avant la création de la table finale.
CREATE TABLE master_data_scraping (
    id SERIAL PRIMARY KEY,

    type TEXT,
    prix TEXT,
    surface TEXT,
    nb_pieces TEXT,
    localisation TEXT,
    details TEXT,
    source VARCHAR(100),
    prix_m2 TEXT,

    date_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- TABLE 3 : golden_data_scraping
-- =========================================================
-- Cette table contient les annonces propres et exploitables.
-- Les champs importants sont convertis en types numériques
-- pour pouvoir faire des calculs : prix, surface, prix au m².
CREATE TABLE golden_data_scraping (
    id SERIAL PRIMARY KEY,

    -- Source de l'annonce : orpi, laforet, century21, etc.
    source VARCHAR(100) NOT NULL,

    -- Caractéristiques principales du bien.
    type VARCHAR(50) NOT NULL,
    prix NUMERIC(12,2) NOT NULL,
    surface NUMERIC(10,2) NOT NULL,
    nb_pieces INTEGER NOT NULL,
    localisation VARCHAR(100) NOT NULL,
    prix_m2 NUMERIC(12,2) NOT NULL,

    -- Date de récupération de l'annonce.
    date_scraping TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index utiles pour les filtres de l'API et de DBeaver.
CREATE INDEX idx_golden_scraping_localisation ON golden_data_scraping (localisation);
CREATE INDEX idx_golden_scraping_source ON golden_data_scraping (source);
CREATE INDEX idx_golden_scraping_surface ON golden_data_scraping (surface);
CREATE INDEX idx_golden_scraping_pieces ON golden_data_scraping (nb_pieces);


-- =========================================================
-- TABLE 4 : dvf_paris_appartements
-- =========================================================
-- Cette table contient les données DVF nettoyées.
-- DVF correspond aux transactions immobilières réelles.
-- Ici, on garde uniquement les ventes d'appartements à Paris.
CREATE TABLE dvf_paris_appartements (
    id SERIAL PRIMARY KEY,

    -- Identifiant et date de la transaction.
    id_mutation VARCHAR(50) NOT NULL,
    date_mutation DATE NOT NULL,

    -- Colonnes utiles pour les analyses dans le temps.
    annee_vente INTEGER NOT NULL,
    mois_vente INTEGER NOT NULL,

    -- Prix total de vente et prix calculé au m².
    valeur_fonciere NUMERIC(12,2) NOT NULL,
    prix_m2 NUMERIC(10,2) NOT NULL,

    -- Caractéristiques du logement vendu.
    surface_reelle_bati NUMERIC(10,2) NOT NULL,
    nombre_pieces_principales INTEGER NOT NULL,
    type_local VARCHAR(50) NOT NULL,

    -- Localisation administrative.
    code_postal VARCHAR(10) NOT NULL,
    arrondissement INTEGER NOT NULL,
    nom_commune VARCHAR(100) NOT NULL,
    adresse_nom_voie TEXT NOT NULL,

    -- Coordonnées géographiques pour afficher les biens sur une carte.
    longitude NUMERIC(10,6) NOT NULL,
    latitude NUMERIC(10,6) NOT NULL
);

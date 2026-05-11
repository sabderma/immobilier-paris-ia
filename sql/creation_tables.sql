DROP TABLE IF EXISTS source_data_scraping;
DROP TABLE IF EXISTS master_data_scraping;
DROP TABLE IF EXISTS golden_data_scraping;

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





CREATE TABLE golden_data_scraping (
    id SERIAL PRIMARY KEY,

    type TEXT NOT NULL,
    prix TEXT NOT NULL,
    surface TEXT NOT NULL,
    nb_pieces TEXT NOT NULL,
    localisation TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    prix_m2 TEXT NOT NULL,

    date_scraping TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);



DROP TABLE IF EXISTS source_data_scraping;

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


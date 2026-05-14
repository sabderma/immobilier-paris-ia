

------------------------- Partie sql source data 

-- Voir les 10 premières annonces
SELECT *
FROM source_data_scraping;



-- Compter le nombre total d'annonces
SELECT COUNT(*) AS nombre_total_annonces
FROM source_data_scraping;


-- Compter le nombre d'annonces par source
SELECT source, COUNT(*) AS nombre_annonces
FROM source_data_scraping
GROUP BY source
ORDER BY nombre_annonces DESC;


-- Voir les sources disponibles
SELECT DISTINCT source
FROM source_data_scraping;


-- Vérifier les valeurs nulles par colonne importante
SELECT
    COUNT(*) AS total_lignes,
    COUNT(*) FILTER (WHERE prix IS NULL) AS prix_null,
    COUNT(*) FILTER (WHERE surface IS NULL) AS surface_null,
    COUNT(*) FILTER (WHERE nb_pieces IS NULL) AS nb_pieces_null,
    COUNT(*) FILTER (WHERE localisation IS NULL) AS localisation_null,
    COUNT(*) FILTER (WHERE source IS NULL) AS source_null
FROM source_data_scraping;




------------------------------------Partie sql master data 




------------------------------------Partie sql golden data 
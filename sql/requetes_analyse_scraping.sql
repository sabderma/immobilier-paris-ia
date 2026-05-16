
-- =========================================================
-- ANALYSE DES VALEURS ABERRANTES 
-- TABLE : golden_data_scraping
-- =========================================================


-- =========================================================
-- 1. PRIX ABERRANTS
-- =========================================================
-- Exemples :
-- prix trop faible
-- prix trop élevé

SELECT *
FROM golden_data_scraping
WHERE prix < 50000
   OR prix > 10000000;



-- =========================================================
-- 2. SURFACES ABERRANTES
-- =========================================================
-- Exemples :
-- surface = 0
-- surface très faible
-- surface énorme

SELECT *
FROM golden_data_scraping
WHERE surface < 9
   OR surface > 500;



-- =========================================================
-- 3. PRIX AU M² ABERRANT
-- =========================================================
-- Exemples :
-- 500 €/m²
-- 100000 €/m²

SELECT *
FROM golden_data_scraping
WHERE prix_m2 < 2000
   OR prix_m2 > 50000;



-- =========================================================
-- 4. NOMBRE DE PIÈCES INCOHÉRENT
-- =========================================================
-- Exemples :
-- 10 pièces pour 20 m²
-- 1 pièce pour 300 m²

SELECT *,
       surface / NULLIF(nb_pieces, 0) AS surface_par_piece
FROM golden_data_scraping
WHERE nb_pieces <= 0
   OR surface / NULLIF(nb_pieces, 0) < 8
   OR surface / NULLIF(nb_pieces, 0) > 80;



-- =========================================================
-- 9. RÉSUMÉ GLOBAL DES ANOMALIES
-- =========================================================

SELECT 'prix_aberrant' AS type_anomalie, COUNT(*) AS total
FROM golden_data_scraping
WHERE prix < 50000
   OR prix > 10000000

UNION ALL

SELECT 'surface_aberrante', COUNT(*)
FROM golden_data_scraping
WHERE surface < 9
   OR surface > 500

UNION ALL

SELECT 'prix_m2_aberrant', COUNT(*)
FROM golden_data_scraping
WHERE prix_m2 < 2000
   OR prix_m2 > 50000

UNION ALL

SELECT 'pieces_incoherentes', COUNT(*)
FROM golden_data_scraping
WHERE nb_pieces <= 0
   OR surface / NULLIF(nb_pieces, 0) < 8
   OR surface / NULLIF(nb_pieces, 0) > 80

UNION ALL

SELECT 'localisation_invalide', COUNT(*)
FROM golden_data_scraping
WHERE localisation IS NULL
   OR localisation = ''
   OR LENGTH(localisation) < 3;

























-- =========================================================
-- SUPPRESSION DES VALEURS ABERRANTES
-- TABLE : golden_data_scraping
-- =========================================================


-- =========================================================
-- 1. SUPPRESSION PRIX ABERRANTS
-- 12 lignes détectées
-- =========================================================

DELETE FROM golden_data_scraping
WHERE prix < 50000
   OR prix > 10000000;



-- =========================================================
-- 2. SUPPRESSION SURFACES ABERRANTES
-- 142 lignes détectées
-- =========================================================

DELETE FROM golden_data_scraping
WHERE surface < 9
   OR surface > 500;



-- =========================================================
-- 3. SUPPRESSION PRIX AU M² ABERRANTS
-- 151 lignes détectées
-- =========================================================

DELETE FROM golden_data_scraping
WHERE prix_m2 < 2000
   OR prix_m2 > 50000;



-- =========================================================
-- 4. SUPPRESSION NOMBRE DE PIÈCES INCOHÉRENT
-- 249 lignes détectées
-- =========================================================

DELETE FROM golden_data_scraping
WHERE nb_pieces <= 0
   OR (
        surface /
        NULLIF(nb_pieces, 0)
      ) < 8
   OR (
        surface /
        NULLIF(nb_pieces, 0)
      ) > 80;



-- =========================================================
-- 5. SUPPRESSION LOCALISATIONS INVALIDES
-- 0 ligne détectée
-- =========================================================

DELETE FROM golden_data_scraping
WHERE localisation IS NULL
   OR localisation = ''
   OR LENGTH(localisation) < 3;



-- =========================================================
-- VÉRIFICATION FINALE
-- =========================================================

SELECT COUNT(*) AS lignes_restantes
FROM golden_data_scraping;
-- =========================================================
-- ANALYSE DES DONNEES ISSUES DU SCRAPING
-- TABLE : golden_data_scraping
-- =========================================================
-- Ce script sert à contrôler les annonces immobilières scrapées.
-- La table golden_data_scraping contient les annonces déjà nettoyées.
--
-- Les premières requêtes affichent les lignes suspectes.
-- La deuxième partie supprime les lignes incohérentes.
-- Il faut donc exécuter les SELECT avant les DELETE pour vérifier
-- ce qui va être supprimé.
-- =========================================================


-- =========================================================
-- 1. PRIX ABERRANTS
-- =========================================================
-- Objectif :
-- repérer les annonces avec un prix total trop faible ou trop élevé.
--
-- Explication simple :
-- Un bien à Paris à moins de 50 000 euros ou à plus de
-- 10 000 000 euros est considéré comme suspect pour cette analyse.
SELECT *
FROM golden_data_scraping
WHERE prix < 50000
   OR prix > 10000000;


-- =========================================================
-- 2. SURFACES ABERRANTES
-- =========================================================
-- Objectif :
-- repérer les annonces avec une surface impossible ou très rare.
--
-- Explication simple :
-- Une surface inférieure à 9 m² est trop petite.
-- Une surface supérieure à 500 m² est très rare pour les annonces
-- de ce projet et peut correspondre à une erreur de scraping.
SELECT *
FROM golden_data_scraping
WHERE surface < 9
   OR surface > 500;


-- =========================================================
-- 3. PRIX AU M² ABERRANT
-- =========================================================
-- Objectif :
-- vérifier si le prix au m² est cohérent.
--
-- Explication simple :
-- Un prix au m² inférieur à 2 000 euros ou supérieur à
-- 50 000 euros est considéré comme suspect.
SELECT *
FROM golden_data_scraping
WHERE prix_m2 < 2000
   OR prix_m2 > 50000;


-- =========================================================
-- 4. NOMBRE DE PIECES INCOHERENT
-- =========================================================
-- Objectif :
-- vérifier si le nombre de pièces est logique avec la surface.
--
-- Explication simple :
-- On calcule la surface moyenne par pièce.
-- Si une pièce fait moins de 8 m² ou plus de 80 m²,
-- l'annonce est considérée comme suspecte.
--
-- NULLIF évite une division par zéro quand nb_pieces vaut 0.
SELECT *,
       surface / NULLIF(nb_pieces, 0) AS surface_par_piece
FROM golden_data_scraping
WHERE nb_pieces <= 0
   OR surface / NULLIF(nb_pieces, 0) < 8
   OR surface / NULLIF(nb_pieces, 0) > 80;


-- =========================================================
-- 5. RESUME GLOBAL DES ANOMALIES
-- =========================================================
-- Objectif :
-- obtenir un tableau avec le nombre d'anomalies par type.
--
-- Explication simple :
-- Cette requête donne une vision globale de la qualité des données
-- avant de supprimer les lignes problématiques.
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
-- Attention :
-- Les requêtes DELETE modifient la base.
-- Elles suppriment les lignes détectées comme incohérentes.
-- Avant de les exécuter, il est préférable de lancer les SELECT
-- de contrôle situés au-dessus.


-- =========================================================
-- 1. SUPPRESSION PRIX ABERRANTS
-- 12 lignes détectées
-- =========================================================
-- Supprime les annonces avec un prix total trop faible ou trop élevé.
DELETE FROM golden_data_scraping
WHERE prix < 50000
   OR prix > 10000000;


-- =========================================================
-- 2. SUPPRESSION SURFACES ABERRANTES
-- 142 lignes détectées
-- =========================================================
-- Supprime les annonces avec une surface impossible ou trop extrême.
DELETE FROM golden_data_scraping
WHERE surface < 9
   OR surface > 500;


-- =========================================================
-- 3. SUPPRESSION PRIX AU M² ABERRANTS
-- 151 lignes détectées
-- =========================================================
-- Supprime les annonces avec un prix au m² incohérent.
DELETE FROM golden_data_scraping
WHERE prix_m2 < 2000
   OR prix_m2 > 50000;


-- =========================================================
-- 4. SUPPRESSION NOMBRE DE PIECES INCOHERENT
-- 249 lignes détectées
-- =========================================================
-- Supprime les annonces où la surface par pièce n'est pas logique.
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
-- Supprime les annonces sans localisation exploitable.
DELETE FROM golden_data_scraping
WHERE localisation IS NULL
   OR localisation = ''
   OR LENGTH(localisation) < 3;


-- =========================================================
-- VERIFICATION FINALE
-- =========================================================
-- Compte le nombre de lignes restantes après nettoyage.
SELECT COUNT(*) AS lignes_restantes
FROM golden_data_scraping;

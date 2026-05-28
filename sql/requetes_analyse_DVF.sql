-- =========================================================
-- ANALYSE DES DONNEES DVF
-- TABLE : dvf_paris_appartements
-- =========================================================
-- Ce script sert à vérifier la qualité des données DVF.
-- Les requêtes recherchent les valeurs incohérentes :
-- prix trop bas, prix trop haut, surface impossible,
-- nombre de pièces incohérent ou coordonnées hors de Paris.
--
-- Important :
-- Ces requêtes servent à contrôler les données.
-- Elles ne modifient pas la base de données.
-- =========================================================


-- =========================================================
-- 1. PRIX AU M² TROP BAS OU TROP HAUT
-- =========================================================
-- Objectif :
-- vérifier si certains appartements ont un prix au m² impossible.
--
-- Explication simple :
-- À Paris, un prix au m² inférieur à 2 000 euros ou supérieur
-- à 40 000 euros est considéré comme suspect dans ce projet.
SELECT *
FROM dvf_paris_appartements
WHERE prix_m2 < 2000
   OR prix_m2 > 40000;


-- =========================================================
-- 2. SURFACE ABERRANTE
-- =========================================================
-- Objectif :
-- trouver les appartements avec une surface trop petite ou trop grande.
--
-- Explication simple :
-- Une surface inférieure à 9 m² est difficilement exploitable.
-- Une surface supérieure à 300 m² est rare pour un appartement
-- et peut indiquer une erreur dans les données.
SELECT *
FROM dvf_paris_appartements
WHERE surface_reelle_bati < 9
   OR surface_reelle_bati > 300;


-- =========================================================
-- 3. PRIX TOTAL INCOHERENT
-- =========================================================
-- Objectif :
-- repérer les ventes avec un prix total anormal.
--
-- Explication simple :
-- Les biens vendus à moins de 50 000 euros ou à plus de
-- 5 000 000 euros sont contrôlés car ils peuvent fausser l'analyse.
SELECT *
FROM dvf_paris_appartements
WHERE valeur_fonciere < 50000
   OR valeur_fonciere > 5000000;


-- =========================================================
-- 4. NOMBRE DE PIECES INCOHERENT
-- =========================================================
-- Objectif :
-- vérifier si le nombre de pièces est logique par rapport à la surface.
--
-- Explication simple :
-- On calcule la surface moyenne par pièce.
-- Si une pièce fait moins de 8 m² ou plus de 80 m²,
-- la ligne est considérée comme suspecte.
--
-- NULLIF évite une division par zéro quand le nombre de pièces vaut 0.
SELECT *,
       surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) AS surface_par_piece
FROM dvf_paris_appartements
WHERE nombre_pieces_principales <= 0
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) < 8
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) > 80;


-- =========================================================
-- 5. COORDONNEES MANQUANTES
-- =========================================================
-- Objectif :
-- trouver les ventes qui ne peuvent pas être placées sur une carte.
--
-- Explication simple :
-- Si la latitude ou la longitude est vide, la ligne pose problème
-- pour les analyses géographiques.
SELECT *
FROM dvf_paris_appartements
WHERE latitude IS NULL
   OR longitude IS NULL;


-- =========================================================
-- 6. COORDONNEES HORS PARIS
-- =========================================================
-- Objectif :
-- vérifier que les points géographiques restent dans Paris.
--
-- Explication simple :
-- Les bornes de latitude et longitude correspondent à une zone
-- autour de Paris. Une vente en dehors de cette zone est suspecte.
SELECT *
FROM dvf_paris_appartements
WHERE latitude NOT BETWEEN 48.80 AND 48.90
   OR longitude NOT BETWEEN 2.20 AND 2.45;


-- =========================================================
-- 7. RESUME DU NOMBRE D'ANOMALIES
-- =========================================================
-- Objectif :
-- obtenir un tableau simple avec le nombre d'anomalies par type.
--
-- Explication simple :
-- UNION ALL permet de regrouper plusieurs comptages dans un seul résultat.
-- Le résultat aide à savoir quelles erreurs sont les plus présentes.
SELECT 'prix_m2_aberrant' AS type_anomalie, COUNT(*) AS total
FROM dvf_paris_appartements
WHERE prix_m2 < 2000 OR prix_m2 > 40000

UNION ALL

SELECT 'surface_aberrante', COUNT(*)
FROM dvf_paris_appartements
WHERE surface_reelle_bati < 9 OR surface_reelle_bati > 300

UNION ALL

SELECT 'prix_total_aberrant', COUNT(*)
FROM dvf_paris_appartements
WHERE valeur_fonciere < 50000 OR valeur_fonciere > 5000000

UNION ALL

SELECT 'coordonnees_manquantes', COUNT(*)
FROM dvf_paris_appartements
WHERE latitude IS NULL OR longitude IS NULL

UNION ALL

SELECT 'coordonnees_hors_paris', COUNT(*)
FROM dvf_paris_appartements
WHERE latitude NOT BETWEEN 48.80 AND 48.90
   OR longitude NOT BETWEEN 2.20 AND 2.45

UNION ALL

SELECT 'Nombre de pièces incohérent' , COUNT(*)
FROM dvf_paris_appartements
WHERE nombre_pieces_principales <= 0
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) < 8
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) > 80;

-- 1. Prix au m² trop bas ou trop haut
SELECT *
FROM dvf_paris_appartements
WHERE prix_m2 < 2000
   OR prix_m2 > 40000;


-- 2. Surface aberrante
SELECT *
FROM dvf_paris_appartements
WHERE surface_reelle_bati < 9
   OR surface_reelle_bati > 300;


-- 3. Prix total incohérent
SELECT *
FROM dvf_paris_appartements
WHERE valeur_fonciere < 50000
   OR valeur_fonciere > 5000000;


--                                              4. Nombre de pièces incohérent
SELECT *,
       surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) AS surface_par_piece
FROM dvf_paris_appartements
WHERE nombre_pieces_principales <= 0
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) < 8
   OR surface_reelle_bati / NULLIF(nombre_pieces_principales, 0) > 80;


-- 5. Coordonnées manquantes
SELECT *
FROM dvf_paris_appartements
WHERE latitude IS NULL
   OR longitude IS NULL;


--                                   6. Coordonnées hors Paris
SELECT *
FROM dvf_paris_appartements
WHERE latitude NOT BETWEEN 48.80 AND 48.90
   OR longitude NOT BETWEEN 2.20 AND 2.45;








-- 7. Résumé du nombre d’anomalies
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







# Documentation simple des scripts SQL

Ce document explique les scripts SQL utilisés dans le projet immobilier Paris.
Le but est de montrer comment les données sont stockées, contrôlées et nettoyées.

## `sql/creation_tables.sql`

Ce script prépare la base de données PostgreSQL.

Il crée 4 tables :

- `source_data_scraping` : stocke les annonces brutes récupérées par scraping.
- `master_data_scraping` : stocke les annonces après un premier nettoyage.
- `golden_data_scraping` : stocke les annonces finales, propres et exploitables.
- `dvf_paris_appartements` : stocke les ventes réelles DVF nettoyées pour les appartements à Paris.

Les tables `source` et `master` gardent beaucoup de colonnes en texte, car les données viennent directement des sites web et peuvent avoir plusieurs formats.

La table `golden_data_scraping` utilise des types numériques pour le prix, la surface, le nombre de pièces et le prix au m². Cela permet ensuite de faire des calculs et des analyses.

La table `dvf_paris_appartements` contient les données officielles DVF avec la date de vente, le prix, la surface, l’arrondissement et les coordonnées géographiques.

## `sql/creation_tables_utilisateurs.sql`

Ce script ajoute les tables liées aux comptes et aux historiques de l'application :

- `users` : stocke les comptes, le mot de passe haché et le rôle `user` ou `admin` ;
- `predictions` : stocke la surface, le nombre de pièces, l'arrondissement et le prix prédit ;
- `exact_address_history` : stocke les adresses exactes validées et leurs coordonnées.

Chaque prédiction et chaque adresse est liée à un compte par `user_id`.
Si un compte est supprimé, ses historiques sont également supprimés grâce à `ON DELETE CASCADE`.

Le script ne supprime aucune table existante. Il peut être ouvert puis exécuté directement dans DBeaver.
Avec Docker, il est exécuté automatiquement uniquement lors de la première création du volume PostgreSQL.

Le backend doit enregistrer uniquement un mot de passe haché avec Argon2 ou bcrypt dans `password_hash`.
Il ne faut jamais enregistrer le mot de passe brut.

## `sql/requetes_analyse_DVF.sql`

Ce script sert à contrôler la qualité des données DVF.

Il recherche :

- les prix au m² trop faibles ou trop élevés ;
- les surfaces trop petites ou trop grandes ;
- les prix de vente incohérents ;
- les nombres de pièces incohérents par rapport à la surface ;
- les coordonnées GPS manquantes ;
- les coordonnées qui ne sont pas dans la zone de Paris.

Le script contient aussi une requête de résumé. Elle compte le nombre d’anomalies par catégorie.

Ces requêtes ne suppriment rien. Elles servent seulement à vérifier les données.

## `sql/requetes_analyse_scraping.sql`

Ce script sert à contrôler les annonces récupérées par scraping.

Il recherche :

- les prix trop bas ou trop élevés ;
- les surfaces incohérentes ;
- les prix au m² incohérents ;
- les nombres de pièces incohérents ;
- les localisations manquantes ou invalides.

La première partie du script affiche les lignes suspectes avec des `SELECT`.

La deuxième partie supprime les lignes incohérentes avec des `DELETE`.
Il faut donc toujours exécuter les requêtes de contrôle avant les requêtes de suppression.

À la fin, une requête compte le nombre de lignes restantes après le nettoyage.

## Pourquoi ces scripts sont importants

Ces scripts prouvent que les données ne sont pas utilisées directement sans contrôle.
Avant l’analyse, le projet vérifie que les prix, les surfaces, les localisations et les coordonnées sont cohérents.

Cela permet d’avoir une base de données plus fiable pour les graphiques, l’API et l’application Streamlit.

# Rapport compétence C4

## 1. Introduction

Dans la compétence C4, le but est de montrer que j'ai créé une base de données
pour stocker les données du projet, que j'ai choisi un système adapté, que j'ai
préparé les imports, et que je peux contrôler les données dans PostgreSQL.

Dans mon projet immobilier Paris IA, la base de données sert à stocker :

- les annonces récupérées par scraping ;
- les annonces après nettoyage ;
- les annonces finales exploitables ;
- les ventes DVF nettoyées ;
- les comptes utilisateurs ;
- les historiques de prédiction ;
- les historiques d'adresses exactes.

J'ai choisi PostgreSQL comme base principale, et j'utilise DBeaver pour ouvrir la
base, voir les tables, lancer des scripts SQL et contrôler les données.

## 2. Fichiers concernés par la C4

Les fichiers principaux de la C4 sont :

| Fichier | Rôle |
| --- | --- |
| `sql/creation_tables.sql` | Crée les tables principales de données immobilières. |
| `sql/creation_tables_utilisateurs.sql` | Crée les tables utilisateurs et historiques. |
| `sql/import_dvf_docker.sql` | Importe les CSV dans PostgreSQL au démarrage Docker. |
| `src/database/db_config.py` | Prépare la connexion PostgreSQL avec les variables d'environnement. |
| `src/database/connexion.py` | Teste la connexion à PostgreSQL. |
| `src/database/import_data_scraping.py` | Importe les fichiers scraping dans PostgreSQL avec pandas. |
| `src/database/import_data_DVF.py` | Importe le fichier DVF final dans PostgreSQL avec pandas. |
| `compose.yml` | Lance PostgreSQL et monte les scripts SQL/imports dans Docker. |
| `docs/bloc1/schema_mcd_mld.drawio` | Schéma MCD et MLD fait avec draw.io. |
| `docs/bloc1/Rapport competence C4 - MCD MLD.md` | Explication simple du MCD et du MLD. |

Le MCD et le MLD sont mis dans un document à part pour garder ce rapport C4
lisible. Le schéma modifiable est dans `docs/bloc1/schema_mcd_mld.drawio`.

## 3. Choix du système de base de données

J'ai choisi **PostgreSQL** pour ce projet.

Pourquoi PostgreSQL :

- il est adapté aux données structurées ;
- il gère bien les tables relationnelles ;
- il permet d'utiliser des types précis comme `NUMERIC`, `DATE`, `TIMESTAMP`,
  `INTEGER` et `VARCHAR` ;
- il permet de créer des index pour accélérer certains filtres ;
- il fonctionne bien avec Python, pandas, SQLAlchemy, FastAPI et DBeaver ;
- il est facile à lancer avec Docker.

Je n'ai pas utilisé un système big data parce que le volume de données reste
raisonnable :

- environ quelques milliers d'annonces immobilières finales ;
- environ 150 000 lignes DVF finales ;
- des requêtes surtout basées sur des filtres, imports et agrégations simples.

PostgreSQL suffit donc largement pour le projet. Un système comme Hadoop, Hive
ou Spark serait plus lourd à installer et pas vraiment nécessaire ici.

## 4. Utilisation de DBeaver

DBeaver me sert d'interface visuelle pour PostgreSQL.

Dans DBeaver, la base doit être visible comme une connexion PostgreSQL. Avec la
configuration Docker du projet, les paramètres attendus sont :

- hôte : `localhost` ;
- port : `5434` ;
- base : valeur de `DB_NAME` dans le fichier `.env` ;
- utilisateur : valeur de `DB_USER` ;
- mot de passe : valeur de `DB_PASSWORD`.

Dans DBeaver, les tables sont normalement visibles ici :

`Connexion PostgreSQL -> Databases -> <nom_base> -> Schemas -> public -> Tables`

Les tables principales attendues sont :

- `source_data_scraping`
- `master_data_scraping`
- `golden_data_scraping`
- `dvf_paris_appartements`
- `users`
- `predictions`
- `exact_address_history`

Je n'ai pas pu vérifier la base en direct depuis l'environnement Codex, car Docker
n'était pas lancé au moment de la vérification. Mais les scripts SQL et Docker
montrent clairement quelles tables doivent apparaître dans DBeaver.

## 4.1 Mes deux façons de travailler : local et Docker

Dans mon projet, il y a deux façons possibles d'utiliser la base PostgreSQL.

### Façon 1 : travail local

En local, j'utilise une base PostgreSQL déjà disponible sur ma machine ou lancée
à part.

Dans ce cas, les scripts Python utilisent :

`src/database/db_config.py`

Ce fichier lit les variables :

- `DATABASE_URL` si elle existe ;
- sinon `DB_USER` ;
- `DB_PASSWORD` ;
- `DB_HOST` ;
- `DB_PORT` ;
- `DB_NAME`.

Dans ce mode, je peux importer les données avec :

```bash
python src/database/import_data_scraping.py
python src/database/import_data_DVF.py
```

Et je peux me connecter avec DBeaver en utilisant les mêmes paramètres que dans
mon fichier `.env`.

### Façon 2 : travail avec Docker

Le fichier `compose.yml` correspond à la façon Docker.

Il ne remplace pas le travail local. Il sert à lancer une version complète du
projet dans des conteneurs :

- PostgreSQL ;
- API FastAPI ;
- interface Streamlit ;
- Prometheus ;
- Grafana.

Pour la compétence C4, la partie importante dans `compose.yml` est surtout le
service `database`.

Ce service :

- lance PostgreSQL avec l'image `postgres:16-alpine` ;
- expose la base sur `localhost:5434` pour DBeaver ;
- garde les données dans le volume `postgres_data` ;
- exécute les scripts SQL au premier démarrage de la base ;
- monte les CSV finaux pour les importer automatiquement.

Donc `compose.yml` sert surtout à montrer la procédure Docker pour créer et
remplir la base. Si je travaille déjà avec une base locale, je ne suis pas
obligé de passer par `compose.yml`.

## 5. Stockage des données immobilières

Les tables immobilières sont créées dans :

`sql/creation_tables.sql`

Ce script prépare quatre tables :

- `source_data_scraping`
- `master_data_scraping`
- `golden_data_scraping`
- `dvf_paris_appartements`

### 5.1 Table `source_data_scraping`

Cette table stocke les annonces brutes ou proches du brut.

Colonnes principales :

- `id`
- `type`
- `prix`
- `surface`
- `nb_pieces`
- `localisation`
- `details`
- `source`
- `prix_m2`
- `date_scraping`

Pourquoi les colonnes sont souvent en `TEXT` :

Les données viennent des sites web. Au début, les valeurs ne sont pas encore
propres. Par exemple, un prix peut être écrit `550 000 €`, une surface peut être
écrite `54 m²`, ou une valeur peut être `non disponible`.

Donc dans la table source, je garde des types souples.

### 5.2 Table `master_data_scraping`

Cette table est une étape intermédiaire.

Elle garde les annonces après un premier nettoyage, mais avant le fichier final.

Elle contient encore :

- `details`
- des colonnes en texte ;
- une date d'import ou de scraping.

Pourquoi :

Le master sert à garder une version plus propre que la source, mais qui garde
encore assez d'information pour faire des corrections.

### 5.3 Table `golden_data_scraping`

Cette table stocke les annonces finales exploitables.

Colonnes principales :

- `id`
- `source`
- `type`
- `prix`
- `surface`
- `nb_pieces`
- `localisation`
- `prix_m2`
- `date_scraping`

Ici, les types sont plus stricts :

- `prix` est en `NUMERIC(12,2)` ;
- `surface` est en `NUMERIC(10,2)` ;
- `nb_pieces` est en `INTEGER` ;
- `prix_m2` est en `NUMERIC(12,2)`.

Pourquoi :

Dans le golden, les données doivent être prêtes pour les calculs. Les colonnes
importantes ne doivent plus rester en texte.

Index créés :

- `idx_golden_scraping_localisation`
- `idx_golden_scraping_source`
- `idx_golden_scraping_surface`
- `idx_golden_scraping_pieces`

Pourquoi :

Ces index aident les filtres utilisés dans l'API : localisation, source, surface
et nombre de pièces.

### 5.4 Table `dvf_paris_appartements`

Cette table stocke les ventes DVF nettoyées.

Colonnes principales :

- `id`
- `id_mutation`
- `date_mutation`
- `annee_vente`
- `mois_vente`
- `valeur_fonciere`
- `prix_m2`
- `surface_reelle_bati`
- `nombre_pieces_principales`
- `type_local`
- `code_postal`
- `arrondissement`
- `nom_commune`
- `adresse_nom_voie`
- `longitude`
- `latitude`

Pourquoi :

Cette table sert aux statistiques, aux cartes, à l'API et au modèle de
prédiction. Elle garde uniquement les ventes d'appartements à Paris.

## 6. Tables utilisateurs et historiques

Les tables utilisateurs sont créées dans :

`sql/creation_tables_utilisateurs.sql`

Ce fichier crée :

- `users`
- `predictions`
- `exact_address_history`

### 6.1 Table `users`

Cette table stocke les comptes utilisateurs.

Colonnes principales :

- `id`
- `email`
- `password_hash`
- `first_name`
- `last_name`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Point technique important :

Le mot de passe n'est pas stocké en clair. La colonne s'appelle
`password_hash`, ce qui veut dire qu'elle doit contenir un mot de passe haché.
Le script précise qu'il ne faut jamais stocker le mot de passe brut.

Il y a aussi une contrainte sur le rôle :

- `user`
- `admin`
- `super_admin`

Il y a un index unique sur `LOWER(email)` pour éviter qu'une même adresse email
soit créée deux fois avec une casse différente.

### 6.2 Table `predictions`

Cette table stocke l'historique des prédictions.

Colonnes principales :

- `id`
- `user_id`
- `surface`
- `nb_pieces`
- `arrondissement`
- `predicted_price`
- `created_at`

Elle contient une clé étrangère vers `users(id)` :

`user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE`

Cela veut dire que si un utilisateur est supprimé, ses prédictions peuvent aussi
être supprimées automatiquement.

### 6.3 Table `exact_address_history`

Cette table stocke les adresses exactes recherchées par l'utilisateur.

Colonnes principales :

- `id`
- `user_id`
- `address`
- `latitude`
- `longitude`
- `created_at`

Elle est liée à `users` avec `ON DELETE CASCADE`, donc si le compte utilisateur
est supprimé, l'historique d'adresses peut aussi être supprimé.

## 7. Import des données avec Docker

Le fichier Docker principal est :

`compose.yml`

Dans le service `database`, PostgreSQL est lancé avec :

- image : `postgres:16-alpine` ;
- port local : `5434` ;
- port interne : `5432`.

Les scripts SQL sont montés dans :

`/docker-entrypoint-initdb.d/`

Dans Docker PostgreSQL, les fichiers dans ce dossier sont exécutés
automatiquement à la première création de la base.

Ordre prévu :

1. `01-creation-tables.sql`
2. `02-import-dvf.sql`
3. `03-creation-tables-utilisateurs.sql`

Les CSV montés dans Docker sont :

- `data/final/dvf_paris_clean_2021_2025.csv`
- `data/final/annonces_scraping_nettoyees_golden.csv`

Pourquoi :

Cela permet de créer la base et d'importer les données automatiquement au
démarrage du conteneur, sans tout faire à la main dans DBeaver.

## 8. Import SQL dans `import_dvf_docker.sql`

Le fichier :

`sql/import_dvf_docker.sql`

fait deux imports :

- import DVF ;
- import scraping golden.

### 8.1 Import DVF

Le script crée d'abord une table temporaire :

`dvf_import`

Puis il utilise :

```sql
COPY dvf_import
FROM '/docker-entrypoint-initdb.d/dvf.csv'
WITH (FORMAT CSV, HEADER TRUE);
```

Ensuite il insère les données dans :

`dvf_paris_appartements`

Pourquoi une table temporaire :

La table temporaire permet de charger le CSV puis de contrôler ou convertir
certaines colonnes avant insertion dans la table finale.

Exemple :

`nombre_pieces_principales::INTEGER`

permet de convertir le nombre de pièces en entier.

### 8.2 Import scraping

Le script crée une table temporaire :

`scraping_import`

Puis il charge :

`/docker-entrypoint-initdb.d/scraping.csv`

Ensuite il insère dans :

`golden_data_scraping`

Pourquoi :

Le fichier golden est déjà nettoyé, donc il peut être importé directement dans
la table finale de scraping.

## 9. Import avec Python

En plus de l'import Docker, j'ai aussi des scripts Python pour importer les CSV.

Ces scripts utilisent :

- `pandas`
- `SQLAlchemy`
- la configuration de connexion dans `src/database/db_config.py`

### 9.1 `import_data_scraping.py`

Ce fichier importe :

- `data/processed/annonces_scraping_fusionnees.csv` vers `source_data_scraping` ;
- `data/processed/annonces_scraping_nettoyees_master.csv` vers `master_data_scraping` ;
- `data/final/annonces_scraping_nettoyees_golden.csv` vers `golden_data_scraping`.

Il utilise :

`df.to_sql(..., if_exists="append", index=False)`

Pourquoi :

Cela permet d'ajouter les données dans PostgreSQL depuis Python, sans passer par
un import manuel dans DBeaver.

### 9.2 `import_data_DVF.py`

Ce fichier importe :

`data/final/dvf_paris_clean_2021_2025.csv`

dans :

`dvf_paris_appartements`

Il utilise aussi :

`df.to_sql(..., if_exists="append", index=False)`

Pourquoi :

Le fichier DVF final est gros, mais pandas peut l'envoyer dans PostgreSQL avec
SQLAlchemy. C'est pratique pour remplir la table depuis le code.

## 10. Connexion PostgreSQL

La connexion est dans :

`src/database/db_config.py`

Ce fichier lit :

- `DATABASE_URL` si elle existe ;
- sinon les variables `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.

Pourquoi :

Je ne mets pas le mot de passe directement dans le code. La connexion utilise
les variables d'environnement ou le fichier `.env`.

Le fichier :

`src/database/connexion.py`

sert à tester la connexion avec :

```sql
SELECT version();
```

Si la connexion marche, il affiche :

`Connexion PostgreSQL réussie !`

## 11. Où les données sont stockées dans DBeaver

DBeaver ne stocke pas lui-même les données. Il sert à voir les données stockées
dans PostgreSQL.

Dans DBeaver, les données doivent être visibles dans le schéma :

`public`

Tables attendues :

| Table | Données stockées |
| --- | --- |
| `source_data_scraping` | Annonces brutes/fusionnées |
| `master_data_scraping` | Annonces après premier nettoyage |
| `golden_data_scraping` | Annonces finales propres |
| `dvf_paris_appartements` | Ventes DVF nettoyées |
| `users` | Comptes utilisateurs |
| `predictions` | Historique des prédictions |
| `exact_address_history` | Historique des adresses exactes |

Pour voir les données dans DBeaver :

1. ouvrir la connexion PostgreSQL ;
2. aller dans le schéma `public` ;
3. ouvrir `Tables` ;
4. clic droit sur une table ;
5. choisir `View Data`.

## 12. Comment lancer ou utiliser la base

Depuis la racine du projet :

```bash
cd /Users/maleksilarbi/Documents/immobilier-paris-ia
```

### 12.1 Si j'utilise Docker

Lancer PostgreSQL avec Docker :

```bash
docker compose up -d database
```

Vérifier l'état du conteneur :

```bash
docker compose ps database
```

Tester la connexion avec Python :

```bash
python src/database/connexion.py
```

### 12.2 Si j'utilise une base locale

Si j'utilise PostgreSQL en local, je n'ai pas besoin de lancer `compose.yml`.

Je vérifie seulement que mon fichier `.env` contient les bons paramètres :

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

Puis je teste la connexion :

```bash
python src/database/connexion.py
```

## 13. Comment importer les données

### 13.1 Import automatique avec Docker

Si le volume PostgreSQL est créé pour la première fois, Docker exécute
automatiquement les scripts dans :

`/docker-entrypoint-initdb.d/`

Donc les tables sont créées et les CSV sont importés automatiquement.

### 13.2 Import manuel avec Python

Cette méthode peut servir en local ou avec Docker, tant que les variables de
connexion pointent vers la bonne base.

Importer le scraping :

```bash
python src/database/import_data_scraping.py
```

Importer le DVF :

```bash
python src/database/import_data_DVF.py
```

### 13.3 Import manuel avec DBeaver

Dans DBeaver, je peux aussi :

1. ouvrir un fichier SQL ;
2. choisir la connexion PostgreSQL ;
3. exécuter `sql/creation_tables.sql` ;
4. exécuter `sql/creation_tables_utilisateurs.sql` ;
5. importer les CSV avec l'assistant d'import si besoin.

## 14. Preuve Git

Les fichiers C4 sont suivis par Git.

Commande :

```bash
git ls-files sql/creation_tables.sql sql/creation_tables_utilisateurs.sql sql/import_dvf_docker.sql src/database/import_data_scraping.py src/database/import_data_DVF.py src/database/db_config.py src/database/connexion.py compose.yml docs/bloc1/schema_mcd_mld.drawio "docs/bloc1/Rapport competence C4 - MCD MLD.md"
```

Résultat :

```text
compose.yml
docs/bloc1/Rapport competence C4 - MCD MLD.md
docs/bloc1/schema_mcd_mld.drawio
sql/creation_tables.sql
sql/creation_tables_utilisateurs.sql
sql/import_dvf_docker.sql
src/database/connexion.py
src/database/db_config.py
src/database/import_data_DVF.py
src/database/import_data_scraping.py
```

## 15. Conclusion personnelle

Pour la compétence C4, j'ai mis en place une base PostgreSQL pour stocker les
données du projet.

J'ai préparé les tables pour les annonces, les DVF, les utilisateurs et les
historiques. J'ai aussi prévu plusieurs façons d'importer les données : Docker,
SQL et Python.

Dans DBeaver, je peux vérifier les tables, consulter les données, et exécuter
les scripts SQL. Cela me permet de montrer que les données sont bien stockées
dans une vraie base PostgreSQL, et pas seulement dans des fichiers CSV.

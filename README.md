# Immobilier Paris IA

Application d'analyse immobiliere sur Paris qui combine les donnees DVF, des
annonces immobilieres scrapees, une API FastAPI, une interface Streamlit et un
modele de prediction de prix base sur XGBoost.

Le projet permet d'explorer les ventes reelles d'appartements a Paris, de les
comparer aux annonces disponibles, de predire un prix indicatif et d'analyser
l'environnement d'une adresse parisienne.

## Fonctionnalites principales

- Carte interactive des ventes DVF a Paris.
- Statistiques par arrondissement, periode, surface et nombre de pieces.
- Tableau et export CSV des donnees DVF filtrees.
- Consultation des annonces immobilieres scrapees et nettoyees.
- Comparaison entre prix des annonces et prix reels DVF.
- Prediction du prix d'un appartement avec un modele XGBoost.
- Analyse d'une adresse exacte avec geocodage, transports, commerces, ecoles et sante.
- Resume de secteur avec OpenAI a partir des donnees calculees par l'application.
- Authentification utilisateur, historique des predictions et historique des adresses.
- Espace administrateur pour suivre les utilisateurs et les historiques.
- Monitoring avec Prometheus et Grafana.
- Livraison Docker et workflows GitHub Actions.

## Technologies utilisees

- Python
- FastAPI
- Streamlit
- PostgreSQL
- Docker et Docker Compose
- Pandas
- Scikit-learn
- XGBoost
- Folium
- OpenAI API
- Prometheus
- Grafana
- GitHub Actions

## Structure du projet

```text
api/            API FastAPI, routes, services, schemas et metriques
streamlit/      Interface utilisateur Streamlit
src/            Collecte, nettoyage, analyse et entrainement du modele
sql/            Creation des tables et import des donnees dans PostgreSQL
data/           Donnees brutes, finales et visualisations
models/         Modele XGBoost et metriques sauvegardees
tests/          Tests unitaires de l'API, de l'auth, du frontend et du modele
monitoring/     Configuration Prometheus et Grafana
docs/           Documentation de livraison, ports, RGPD et competences
scripts/        Scripts utilitaires, dont purge RGPD et rapport de livraison modele
```

## Variables d'environnement

Le projet utilise un fichier `.env` local. Ce fichier ne doit pas etre versionne
et ne doit jamais contenir de vraies cles dans le README.

Exemple de `.env` a adapter :

```env
DB_USER=postgres
DB_PASSWORD=mot_de_passe_a_remplacer
DB_NAME=immobilier_paris

API_KEY=cle_api_a_remplacer
JWT_SECRET_KEY=secret_jwt_a_remplacer

IDFM_API_KEY=cle_idfm_a_remplacer
OPENAI_API_KEY=cle_openai_a_remplacer
OPENAI_MODEL=gpt-5.4-mini

SUPER_ADMIN_EMAIL=admin@example.com
SUPER_ADMIN_PASSWORD=mot_de_passe_admin_a_remplacer

GRAFANA_ADMIN_PASSWORD=mot_de_passe_grafana_a_remplacer
```

Important : les valeurs ci-dessus sont des exemples. Les vraies valeurs doivent
rester uniquement sur la machine locale, le serveur ou les secrets GitHub.

Choix de connexion PostgreSQL selon le contexte :

| Contexte | DB_HOST | DB_PORT | Explication |
|---|---|---:|---|
| API dans Docker local | `database` | `5432` | Compose force ces valeurs dans le conteneur API. |
| API sur le PC vers PostgreSQL Docker | `127.0.0.1` | `5434` | Le conteneur PostgreSQL expose son port interne `5432` sur le port local `5434`. |
| API sur le PC vers PostgreSQL installe sur le PC | `localhost` | `5433` | Port utilise par la base PostgreSQL locale du PC dans cette configuration. |
| API en production Docker | `database` | `5432` | Compose production force ces valeurs dans le conteneur API. |

Dans Docker, il ne faut pas remplacer `database:5432` par `localhost:5434` :
`localhost` designerait le conteneur API lui-meme, pas le conteneur PostgreSQL.

La meme logique existe pour les autres services :

| Service | Adresse entre conteneurs Docker | Adresse depuis le PC en Docker local | Adresse sur le VPS en production |
|---|---|---|---|
| PostgreSQL | `database:5432` | `localhost:5434` | `127.0.0.1:5434` |
| API FastAPI | `api:8000` | `localhost:8002` | `127.0.0.1:8002` |
| Streamlit | `streamlit:8501` | `localhost:8501` | `127.0.0.1:8501` |
| Prometheus | `prometheus:9090` | `localhost:9090` | `127.0.0.1:9090` |
| Grafana | `grafana:3000` | `localhost:3000` | `127.0.0.1:3000` |

En production, Nginx expose seulement le site public et redirige vers Streamlit.
Les autres services restent accessibles depuis le VPS ou avec un tunnel SSH.

## Lancement local avec Docker

Depuis la racine du projet :

```bash
docker compose up -d --build
```

Cette commande lance :

- PostgreSQL
- l'API FastAPI
- l'interface Streamlit
- Prometheus
- Grafana

Pour voir l'etat des conteneurs :

```bash
docker compose ps
```

Pour afficher les logs :

```bash
docker compose logs -f
```

Pour arreter l'application :

```bash
docker compose down
```

## URLs utiles en local

| Service | URL |
|---|---|
| Interface Streamlit | `http://localhost:8501` |
| API FastAPI | `http://localhost:8002` |
| Documentation Swagger | `http://localhost:8002/docs` |
| Health check API | `http://localhost:8002/health` |
| Metriques API | `http://localhost:8002/metrics` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |
| PostgreSQL | `localhost:5434` |

## Lancement manuel en local

Il est possible de lancer seulement l'API et Streamlit sans Docker complet, a
condition d'avoir une base PostgreSQL disponible et les variables `.env`
correctement configurees.

API FastAPI :

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Interface Streamlit :

```bash
streamlit run streamlit/app.py --server.address=127.0.0.1 --server.port=8501
```

## Tests

Pour lancer toute la suite de tests :

```bash
python3 -m unittest discover -s tests -p "test*.py"
```

Tests principaux :

```bash
python3 -m unittest discover -s tests -p "test_api.py" -v
python3 -m unittest discover -s tests -p "test_auth.py" -v
python3 -m unittest discover -s tests -p "test_streamlit_frontend.py" -v
python3 -m unittest discover -s tests -p "test_prediction.py" -v
python3 -m unittest discover -s tests -p "test_donnees_livraison.py" -v
```

## Donnees et modele

Les donnees finales utilisees par l'application sont dans :

```text
data/final/
```

Fichiers principaux :

- `dvf_paris_clean_2021_2025.csv` : ventes DVF nettoyees.
- `annonces_scraping_nettoyees_golden.csv` : annonces immobilieres nettoyees.
- `commerces_paris_secours.json` : donnees de secours pour les commerces.

Le modele de prediction est stocke dans :

```text
models/xgboost_prix_dvf.joblib
models/xgboost_prix_dvf_metrics.json
```

## API

L'API expose notamment :

- `/health` : verification de l'API et de PostgreSQL.
- `/metrics` : metriques Prometheus.
- `/dvf/filtres` : filtres disponibles pour les ventes DVF.
- `/dvf/points` : points cartographiques DVF.
- `/dvf/export.csv` : export CSV des ventes.
- `/scraping/annonces` : annonces immobilieres nettoyees.
- `/stats/dvf/resume` : statistiques DVF.
- `/prediction/prix` : prediction du prix d'un appartement.
- `/geocodage/adresse` : analyse d'une adresse exacte.
- `/auth/register`, `/auth/login`, `/auth/me` : authentification.
- `/admin/overview` : espace administrateur.

Les routes de donnees sont protegees avec l'en-tete :

```http
X-API-Key: cle_api_a_remplacer
```

## Monitoring

Prometheus collecte les metriques exposees par l'API sur `/metrics`.
Grafana affiche les dashboards de suivi de l'application, du modele et des
appels OpenAI.

Les fichiers de configuration sont dans :

```text
monitoring/
```

## Livraison et documentation

Les fichiers Docker principaux sont :

- `compose.yml` pour le lancement local.
- `compose.prod.yml` pour la production.
- `Dockerfile.api` pour l'image FastAPI.
- `Dockerfile.streamlit` pour l'image Streamlit.

La documentation detaillee se trouve dans :

- `docs/Document ports et lancements essentiels.md`
- `docs/Document mise en ligne VPS.md`
- `docs/bloc1/`
- `docs/bloc2/`
- `docs/bloc3/`

## Securite

- Le fichier `.env` ne doit pas etre commite.
- Les vraies cles API ne doivent jamais apparaitre dans le README.
- Les mots de passe sont hashes cote backend avec Argon2.
- Les tokens JWT sont signes avec `JWT_SECRET_KEY`.
- L'espace administrateur est reserve aux roles `admin` et `super_admin`.
- Un script de purge RGPD est disponible dans `scripts/purge_donnees_rgpd.py`.

## Auteur

Projet realise par Malek Silarbi.

# Document ports et lancements essentiels

## 1. Objectif du document

Ce document explique les ports utilises par mon application et les commandes
importantes pour lancer chaque partie.

Je parle de trois cas :

- lancement avec Docker en local ;
- lancement manuel sur mon PC local ;
- lancement en ligne sur le VPS ;
- integration avec GitHub Actions.

Le but est de savoir rapidement :

- quel port est utilise par chaque service ;
- comment lancer l'application complete ;
- comment lancer seulement l'API ;
- comment lancer Streamlit ;
- comment voir la documentation API ;
- comment ouvrir Prometheus ;
- comment ouvrir Grafana ;
- comment verifier la base PostgreSQL ;
- comment verifier l'application en ligne.

## 2. Resume des ports utilises

| Service | Port interne Docker | Port local Docker | Port production VPS | Role |
|---|---:|---:|---:|---|
| PostgreSQL | `5432` | `5434` | `127.0.0.1:5434` | Base de donnees. |
| API FastAPI | `8000` | `8002` | `127.0.0.1:8002` | API REST. |
| Streamlit | `8501` | `8501` | `127.0.0.1:8501` | Interface utilisateur. |
| Prometheus | `9090` | `9090` | `127.0.0.1:9090` | Metriques. |
| Grafana | `3000` | `3000` | `127.0.0.1:3000` | Dashboards. |
| Nginx | `80 / 443` | non utilise en local Docker | `80 / 443` | Acces public HTTPS. |
| SSH | `22` | non utilise par l'application | `22` | Connexion au VPS. |

Point important :

- dans Docker, l'API tourne dans le conteneur sur le port `8000` ;
- sur mon PC, elle est accessible sur `http://localhost:8002` ;
- en production, elle reste accessible seulement depuis le VPS sur
  `127.0.0.1:8002`.

La logique est la meme pour tous les services : il faut distinguer l'adresse
interne Docker, l'adresse vue depuis mon PC et l'adresse locale du VPS.

| Service | Adresse entre conteneurs Docker | Adresse depuis mon PC en Docker local | Adresse locale sur le VPS |
|---|---|---|---|
| PostgreSQL | `database:5432` | `localhost:5434` | `127.0.0.1:5434` |
| API FastAPI | `api:8000` | `localhost:8002` | `127.0.0.1:8002` |
| Streamlit | `streamlit:8501` | `localhost:8501` | `127.0.0.1:8501` |
| Prometheus | `prometheus:9090` | `localhost:9090` | `127.0.0.1:9090` |
| Grafana | `grafana:3000` | `localhost:3000` | `127.0.0.1:3000` |

Exemple important :

- Streamlit dans Docker appelle l'API avec `http://api:8000` ;
- mon navigateur appelle l'API avec `http://localhost:8002` ;
- Prometheus dans Docker collecte les metriques avec `api:8000` ;
- Grafana dans Docker parle a Prometheus avec `prometheus:9090`.

## 3. Ports en Docker local

Le fichier utilise est :

```text
compose.yml
```

Il expose les services comme ca :

| Service Docker | Port vu depuis mon PC | Exemple d'URL |
|---|---|---|
| `database` | `localhost:5434` | DBeaver ou psql |
| `api` | `localhost:8002` | `http://localhost:8002` |
| `streamlit` | `localhost:8501` | `http://localhost:8501` |
| `prometheus` | `localhost:9090` | `http://localhost:9090` |
| `grafana` | `localhost:3000` | `http://localhost:3000` |

Le port `5432` est le port interne normal de PostgreSQL.
Mais sur mon PC, j'utilise `5434` pour eviter un conflit avec une autre base
PostgreSQL locale.

## 4. Lancer toute l'application en Docker local

Depuis le dossier du projet :

```bash
cd /Users/maleksilarbi/Documents/immobilier-paris-ia
docker compose up -d --build
```

Cette commande lance :

- PostgreSQL ;
- FastAPI ;
- Streamlit ;
- Prometheus ;
- Grafana.

Pour voir l'etat des services :

```bash
docker compose ps
```

Pour voir tous les logs :

```bash
docker compose logs -f
```

Pour arreter :

```bash
docker compose down
```

## 5. Lancer seulement certains services Docker

Lancer seulement la base PostgreSQL :

```bash
docker compose up -d database
```

Lancer seulement l'API :

```bash
docker compose up -d api
```

Lancer seulement Streamlit :

```bash
docker compose up -d streamlit
```

Lancer Prometheus et Grafana :

```bash
docker compose up -d prometheus grafana
```

Relancer un service :

```bash
docker compose restart api
docker compose restart streamlit
docker compose restart prometheus
docker compose restart grafana
```

Reconstruire un service apres modification :

```bash
docker compose up -d --build api
docker compose up -d --build streamlit
```

## 6. URLs essentielles en Docker local

Quand Docker local est lance :

| Besoin | URL |
|---|---|
| Application Streamlit | `http://localhost:8501` |
| API FastAPI | `http://localhost:8002` |
| Documentation Swagger API | `http://localhost:8002/docs` |
| Documentation ReDoc API | `http://localhost:8002/redoc` |
| Health check API | `http://localhost:8002/health` |
| Metriques API | `http://localhost:8002/metrics` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |
| PostgreSQL pour DBeaver | `localhost:5434` |

## 7. Recapitulatif direct par service

Cette partie sert a retrouver vite comment lancer et comment ouvrir chaque outil.

| Service | Docker local | PC local manuel | Production / VPS |
|---|---|---|---|
| PostgreSQL | `docker compose up -d database` puis DBeaver sur `localhost:5434` | garder `database` dans Docker, puis utiliser `DB_HOST=127.0.0.1` et `DB_PORT=5434` | tunnel SSH `ssh -L 5434:127.0.0.1:5434 ubuntu@164.132.42.47`, puis DBeaver sur `127.0.0.1:5434` |
| API FastAPI | `docker compose up -d api`, puis `http://localhost:8002/docs` | `uvicorn api.main:app --reload --host 127.0.0.1 --port 8000`, puis `http://127.0.0.1:8000/docs` | tunnel SSH `ssh -L 8002:127.0.0.1:8002 ubuntu@164.132.42.47`, puis `http://127.0.0.1:8002/docs` |
| Streamlit | `docker compose up -d streamlit`, puis `http://localhost:8501` | `streamlit run streamlit/app.py --server.address=127.0.0.1 --server.port=8501` | site public `https://dvfvisionparis.fr` |
| Prometheus | `docker compose up -d prometheus`, puis `http://localhost:9090` | conseille de le garder avec Docker, car il lit `api:8000` dans le reseau Docker | tunnel SSH `ssh -L 9090:127.0.0.1:9090 ubuntu@164.132.42.47`, puis `http://127.0.0.1:9090` |
| Grafana | `docker compose up -d grafana`, puis `http://localhost:3000` | conseille de le garder avec Docker, car il lit Prometheus | tunnel SSH `ssh -L 3000:127.0.0.1:3000 ubuntu@164.132.42.47`, puis `http://127.0.0.1:3000` |

Pour voir les tables PostgreSQL en local, le plus simple est DBeaver :

```text
Host : localhost
Port : 5434
Database : DB_NAME
User : DB_USER
Password : DB_PASSWORD
```

Pour voir les tables PostgreSQL de production depuis le PC, il faut d'abord
ouvrir le tunnel SSH :

```bash
ssh -L 5434:127.0.0.1:5434 ubuntu@164.132.42.47
```

Puis dans DBeaver :

```text
Host : 127.0.0.1
Port : 5434
Database : DB_NAME
User : DB_USER
Password : DB_PASSWORD
```

Donc pour les tableaux de la base, la logique est :

- local Docker : DBeaver se connecte directement a `localhost:5434` ;
- production : DBeaver passe par un tunnel SSH, puis se connecte a
  `127.0.0.1:5434` ;
- l'API et Streamlit ne se connectent pas avec DBeaver, ils utilisent les
  variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

## 8. Voir la documentation API

Avec Docker local :

```text
http://localhost:8002/docs
```

Cette page est la documentation Swagger de FastAPI.

Elle permet de voir :

- les routes disponibles ;
- les parametres attendus ;
- les methodes `GET`, `POST`, `PATCH`, `DELETE` ;
- les reponses de l'API.

Autre documentation :

```text
http://localhost:8002/redoc
```

## 9. Tester l'API en local Docker

Verifier que l'API fonctionne :

```bash
curl http://localhost:8002/health
```

Verifier la page d'accueil API :

```bash
curl http://localhost:8002/
```

Verifier les metriques :

```bash
curl http://localhost:8002/metrics
```

Verifier une route protegee avec la cle API :

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8002/commerces/paris
```

Si `$API_KEY` n'est pas charge dans le terminal, il faut soit exporter la
variable, soit remplacer `$API_KEY` par la valeur du fichier `.env`.

## 10. Grafana en local Docker

Grafana se lance avec Docker Compose.

Commande :

```bash
docker compose up -d grafana
```

Adresse :

```text
http://localhost:3000
```

Identifiant :

```text
admin
```

Le mot de passe vient de la variable :

```text
GRAFANA_ADMIN_PASSWORD
```

Cette variable est dans le fichier `.env`.

Grafana affiche les dashboards de monitoring :

- dashboard de l'application ;
- dashboard du modele IA ;
- etat de l'API ;
- erreurs HTTP ;
- latence ;
- etat PostgreSQL.

## 11. Prometheus en local Docker

Prometheus se lance avec Docker Compose.

Commande :

```bash
docker compose up -d prometheus
```

Adresse :

```text
http://localhost:9090
```

Prometheus lit les metriques de l'API sur :

```text
http://api:8000/metrics
```

Attention : `api:8000` est une adresse interne Docker.
Depuis mon navigateur, l'API est sur `localhost:8002`.
Mais depuis Prometheus, qui est aussi dans Docker, il faut utiliser le nom du
service Docker `api`.

## 12. PostgreSQL et DBeaver en local Docker

La base PostgreSQL tourne dans Docker.

Depuis mon PC ou DBeaver, la connexion se fait avec :

```text
Host : localhost
Port : 5434
Database : valeur de DB_NAME
User : valeur de DB_USER
Password : valeur de DB_PASSWORD
```

Pour ouvrir PostgreSQL depuis le terminal :

```bash
docker compose exec database psql -U "$DB_USER" -d "$DB_NAME"
```

Commandes SQL utiles :

```sql
\dt
SELECT COUNT(*) FROM dvf_paris_appartements;
SELECT COUNT(*) FROM golden_data_scraping;
SELECT COUNT(*) FROM users;
```

## 13. Logs essentiels en Docker local

Voir les logs API :

```bash
docker compose logs -f api
```

Voir les logs Streamlit :

```bash
docker compose logs -f streamlit
```

Voir les logs PostgreSQL :

```bash
docker compose logs -f database
```

Voir les logs Prometheus :

```bash
docker compose logs -f prometheus
```

Voir les logs Grafana :

```bash
docker compose logs -f grafana
```

## 14. Lancement manuel sur mon PC local

Le lancement manuel sert surtout pour developper sans relancer toute l'image
Docker.

Dans ce cas, PostgreSQL peut rester dans Docker, pendant que l'API et Streamlit
tournent directement sur le PC.

Etape 1 : lancer seulement la base.

```bash
docker compose up -d database
```

Etape 2 : creer ou activer l'environnement Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Etape 3 : charger les variables locales.

```bash
set -a
source .env
set +a
```

Etape 4 : adapter la connexion base pour le PC local.

Quand l'API tourne hors Docker, il y a deux cas possibles.

Cas 1 : l'API du PC parle a PostgreSQL lance dans Docker local.

```text
DB_HOST=127.0.0.1
DB_PORT=5434
```

Cas 2 : l'API du PC parle a PostgreSQL installe directement sur le PC.

```text
DB_HOST=localhost
DB_PORT=5433
```

Quand l'API tourne dans Docker, elle utilise plutot :

```text
DB_HOST=database
DB_PORT=5432
```

Donc la regle est :

- `5433` pour PostgreSQL installe sur le PC dans ma configuration locale ;
- `5434` pour PostgreSQL Docker vu depuis le PC ou DBeaver ;
- `5432` pour PostgreSQL vu depuis les autres conteneurs Docker.

## 15. Lancer FastAPI manuellement sur PC

Mode simple sur le port `8000` :

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Documentation API :

```text
http://127.0.0.1:8000/docs
```

Health check :

```text
http://127.0.0.1:8000/health
```

Mode proche de Docker local sur le port `8002` :

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8002
```

Dans ce cas, la documentation API est :

```text
http://127.0.0.1:8002/docs
```

## 16. Lancer Streamlit manuellement sur PC

Si l'API manuelle tourne sur `8000`, Streamlit peut utiliser la valeur par
defaut :

```bash
streamlit run streamlit/app.py --server.address=127.0.0.1 --server.port=8501
```

Adresse :

```text
http://127.0.0.1:8501
```

Si l'API tourne sur `8002`, il faut indiquer l'URL API :

```bash
API_BASE_URL=http://127.0.0.1:8002 streamlit run streamlit/app.py --server.address=127.0.0.1 --server.port=8501
```

Dans tous les cas, Streamlit utilise aussi `API_KEY` pour appeler les routes
protegees de FastAPI.

## 17. Prometheus et Grafana en mode PC local manuel

Le mode le plus simple est de lancer Prometheus et Grafana avec Docker Compose.

Commande :

```bash
docker compose up -d prometheus grafana
```

Mais attention : la configuration actuelle de Prometheus vise l'API Docker avec :

```text
api:8000
```

Donc si l'API tourne manuellement sur le PC, Prometheus Docker ne verra pas
forcement l'API manuelle sans adaptation.

Pour le monitoring, le lancement conseille est donc :

```bash
docker compose up -d --build
```

Comme ca, API, Prometheus et Grafana sont dans le meme reseau Docker.

## 18. Ports occupes sur mon PC local

Quand toute l'application Docker tourne, ces ports sont occupes :

```text
5434  PostgreSQL
8002  API FastAPI
8501  Streamlit
9090  Prometheus
3000  Grafana
```

Pour verifier si un port est deja utilise sur macOS :

```bash
lsof -i :8501
lsof -i :8002
lsof -i :5434
lsof -i :9090
lsof -i :3000
```

Pour arreter proprement les services Docker :

```bash
docker compose down
```

Si un ancien processus manuel bloque un port, `lsof` permet de le retrouver
puis de l'arreter.

## 19. Integration avec GitHub

Les workflows GitHub sont dans :

```text
.github/workflows/
```

Les fichiers importants sont :

| Workflow | Role |
|---|---|
| `tests-application.yml` | Lance les tests application. |
| `livraison-modele.yml` | Valide et livre le modele IA. |
| `livraison-application.yml` | Construit les images Docker et deploie sur le VPS. |

GitHub Actions ne garde pas une application ouverte comme mon PC.
Il lance des jobs temporaires.

Dans GitHub, les ports ne sont pas faits pour etre ouverts au public.
GitHub sert surtout a :

- installer les dependances ;
- lancer les tests ;
- verifier Docker Compose ;
- construire les images Docker ;
- publier les images dans GHCR ;
- se connecter au VPS en SSH ;
- demander au VPS de relancer Docker Compose.

## 20. Commandes GitHub essentielles

Pour declencher GitHub Actions avec un push :

```bash
git status
git add .
git commit -m "update application"
git push origin main
```

Dans GitHub Actions, le workflow lance notamment :

```bash
python -m unittest discover -s tests -p "test_api.py" -v
python -m unittest discover -s tests -p "test_auth.py" -v
python -m unittest discover -s tests -p "test_streamlit_frontend.py" -v
python -m unittest discover -s tests -p "test_donnees_livraison.py" -v
python -m unittest discover -s tests -p "test_prediction.py" -v
docker compose -f compose.yml config
docker compose -f compose.prod.yml config
```

Puis il construit et publie :

```text
ghcr.io/sabderma/immobilier-paris-api:latest
ghcr.io/sabderma/immobilier-paris-streamlit:latest
```

## 21. Integration sur le VPS en ligne

En production, le fichier utilise est :

```text
compose.prod.yml
```

Les ports sont volontairement limites a `127.0.0.1`.

Cela veut dire :

- le service tourne sur le VPS ;
- il n'est pas expose directement sur Internet ;
- Nginx est le seul point d'entree public pour l'application.

Ports production :

| Service | Port sur le VPS | Public ? |
|---|---|---|
| Nginx HTTP | `80` | oui |
| Nginx HTTPS | `443` | oui |
| SSH | `22` | oui, pour administration |
| Streamlit | `127.0.0.1:8501` | non |
| API | `127.0.0.1:8002` | non |
| PostgreSQL | `127.0.0.1:5434` | non |
| Prometheus | `127.0.0.1:9090` | non |
| Grafana | `127.0.0.1:3000` | non |

## 22. Lancer l'application en ligne sur le VPS

Connexion au VPS :

```bash
ssh ubuntu@164.132.42.47
```

Aller dans le dossier de production :

```bash
cd /home/ubuntu/immobilier-paris-ia
```

Recuperer les images et lancer :

```bash
docker compose -f compose.prod.yml pull
docker compose -f compose.prod.yml up -d
docker compose -f compose.prod.yml ps
```

Voir les logs :

```bash
docker compose -f compose.prod.yml logs -f
```

Redemarrer :

```bash
docker compose -f compose.prod.yml restart
```

## 23. Acces public en ligne

L'application publique est :

```text
https://dvfvisionparis.fr
```

Nginx ecoute sur :

```text
80
443
```

Puis Nginx redirige vers :

```text
http://127.0.0.1:8501
```

Donc Streamlit reste local au VPS, mais le site est public grace a Nginx.

Verification :

```bash
curl -I https://dvfvisionparis.fr
```

## 24. Documentation API en production

En production, l'API n'est pas exposee directement sur Internet.

Donc depuis mon navigateur, je ne vais pas directement sur :

```text
https://dvfvisionparis.fr/docs
```

La documentation API reste accessible depuis le VPS :

```bash
curl http://127.0.0.1:8002/docs
```

Pour la voir dans le navigateur local, il faut faire un tunnel SSH :

```bash
ssh -L 8002:127.0.0.1:8002 ubuntu@164.132.42.47
```

Puis ouvrir :

```text
http://127.0.0.1:8002/docs
```

## 25. Grafana en production

Grafana tourne sur le VPS :

```text
127.0.0.1:3000
```

Il n'est pas public.

Pour y acceder depuis le PC local, il faut faire un tunnel SSH :

```bash
ssh -L 3000:127.0.0.1:3000 ubuntu@164.132.42.47
```

Puis ouvrir :

```text
http://127.0.0.1:3000
```

Identifiant :

```text
admin
```

Mot de passe :

```text
GRAFANA_ADMIN_PASSWORD
```

## 26. Prometheus en production

Prometheus tourne sur :

```text
127.0.0.1:9090
```

Pour y acceder depuis mon PC :

```bash
ssh -L 9090:127.0.0.1:9090 ubuntu@164.132.42.47
```

Puis ouvrir :

```text
http://127.0.0.1:9090
```

Verifier Prometheus depuis le VPS :

```bash
curl http://127.0.0.1:9090/-/ready
```

## 27. PostgreSQL production avec DBeaver

PostgreSQL production est sur :

```text
127.0.0.1:5434
```

Il n'est pas public.

Pour l'ouvrir avec DBeaver depuis le PC local, il faut faire un tunnel SSH :

```bash
ssh -L 5434:127.0.0.1:5434 ubuntu@164.132.42.47
```

Puis dans DBeaver :

```text
Host : 127.0.0.1
Port : 5434
Database : DB_NAME
User : DB_USER
Password : DB_PASSWORD
```

## 28. Verification production essentielle

Depuis le VPS :

```bash
cd /home/ubuntu/immobilier-paris-ia
docker compose -f compose.prod.yml ps
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:9090/-/ready
curl -I http://127.0.0.1:8501
curl -I https://dvfvisionparis.fr
```

Voir les logs importants :

```bash
docker compose -f compose.prod.yml logs -f api
docker compose -f compose.prod.yml logs -f streamlit
docker compose -f compose.prod.yml logs -f database
docker compose -f compose.prod.yml logs -f prometheus
docker compose -f compose.prod.yml logs -f grafana
```

## 29. Nginx en production

Nginx gere le domaine public.

Fichier de configuration :

```text
/etc/nginx/sites-available/dvfvisionparis.fr
```

Commandes essentielles :

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx
```

HTTPS avec Certbot :

```bash
sudo certbot --nginx -d dvfvisionparis.fr
```

Nginx redirige vers Streamlit :

```text
http://127.0.0.1:8501
```

## 30. Commandes rapides par besoin

| Besoin | Commande ou URL |
|---|---|
| Lancer tout en Docker local | `docker compose up -d --build` |
| Voir Streamlit local | `http://localhost:8501` |
| Voir API docs local Docker | `http://localhost:8002/docs` |
| Voir Prometheus local | `http://localhost:9090` |
| Voir Grafana local | `http://localhost:3000` |
| Voir les conteneurs | `docker compose ps` |
| Voir logs API | `docker compose logs -f api` |
| Arreter Docker local | `docker compose down` |
| Lancer API PC local | `uvicorn api.main:app --reload --port 8000` |
| Lancer Streamlit PC local | `streamlit run streamlit/app.py --server.port=8501` |
| Lancer production VPS | `docker compose -f compose.prod.yml up -d` |
| Voir site en ligne | `https://dvfvisionparis.fr` |
| Voir API docs production | tunnel SSH vers port `8002` |
| Voir Grafana production | tunnel SSH vers port `3000` |
| Voir Prometheus production | tunnel SSH vers port `9090` |

## 31. Conclusion

Les ports principaux de mon application sont :

- `8501` pour Streamlit ;
- `8002` pour l'API vue depuis le PC ou le VPS ;
- `8000` pour l'API a l'interieur de Docker ;
- `5434` pour PostgreSQL vu depuis le PC ou le VPS ;
- `5432` pour PostgreSQL a l'interieur de Docker ;
- `9090` pour Prometheus ;
- `3000` pour Grafana ;
- `80` et `443` pour Nginx en production ;
- `22` pour SSH.

En local, tout peut se lancer avec Docker Compose.

Sur le PC local, l'API et Streamlit peuvent aussi etre lances manuellement pour
developper.

Sur GitHub, les workflows testent, construisent et publient les images.

Sur le VPS, Docker Compose lance les services, et Nginx rend Streamlit public
avec HTTPS.

# Déploiement VPS avec GitHub Actions

## Objectif

Mettre l'application en ligne sur le VPS Ubuntu avec Docker Compose, puis
laisser GitHub Actions la mettre à jour automatiquement après un push sur
`main`.

## Principe simple

```text
push sur GitHub
  -> tests application C18
  -> validation modele IA C13
  -> build et publication Docker C19
  -> connexion SSH au VPS
  -> docker compose pull
  -> docker compose up -d
```

## VPS utilise

```text
Utilisateur SSH : ubuntu
Adresse : 164.132.42.47
Dossier de production : /home/ubuntu/immobilier-paris-ia
```

Le VPS contient un fichier `.env` de production. Ce fichier reste uniquement sur
le serveur et ne doit pas être commit dans Git.

## Cle SSH de deploiement

Une clé SSH dédiée au déploiement GitHub Actions a été créée localement :

```text
/Users/maleksilarbi/.ssh/immobilier_paris_github_actions_deploy
```

Sa clé publique a été ajoutée au fichier `authorized_keys` du VPS.

## Secrets GitHub a créer

Dans GitHub :

```text
Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret
```

Créer les secrets suivants :

```text
DEPLOY_HOST=164.132.42.47
DEPLOY_USER=ubuntu
DEPLOY_PATH=/home/ubuntu/immobilier-paris-ia
DEPLOY_SSH_KEY=<contenu de la cle privee>
```

Pour `DEPLOY_SSH_KEY`, utiliser le contenu complet du fichier :

```text
/Users/maleksilarbi/.ssh/immobilier_paris_github_actions_deploy
```

Le contenu commence par :

```text
-----BEGIN OPENSSH PRIVATE KEY-----
```

et se termine par :

```text
-----END OPENSSH PRIVATE KEY-----
```

## Variable GitHub a créer

Dans GitHub :

```text
Settings -> Secrets and variables -> Actions -> Variables -> New repository variable
```

Créer :

```text
DEPLOY_APPLICATION=true
```

Cette variable active le job `deployer-serveur`.

## Fichiers envoyes au serveur par GitHub Actions

Avant de relancer Docker, GitHub Actions envoie au VPS :

```text
compose.prod.yml
sql/
data/final/
monitoring/
```

Le fichier `.env` n'est pas envoyé depuis GitHub.

## Commandes executees sur le VPS

GitHub Actions se connecte au VPS et exécute :

```bash
docker compose -f compose.prod.yml pull
docker compose -f compose.prod.yml up -d
docker compose -f compose.prod.yml ps
```

## Verification apres deploiement

Sur le VPS :

```bash
cd /home/ubuntu/immobilier-paris-ia
docker compose -f compose.prod.yml ps
```

Services attendus :

```text
database
api
streamlit
prometheus
grafana
```

## Acces aux services

En production, seul Streamlit est accessible directement depuis Internet :

```text
Streamlit : http://164.132.42.47:8501
```

Les autres services sont limites au VPS avec `127.0.0.1` :

```text
API : http://127.0.0.1:8002
Grafana : http://127.0.0.1:3000
Prometheus : http://127.0.0.1:9090
PostgreSQL : 127.0.0.1:5434
```

Cela evite d'exposer la base de donnees, Prometheus et l'API directement sur
Internet.

Pour ouvrir Grafana depuis son ordinateur, utiliser un tunnel SSH :

```bash
ssh -i ~/.ssh/immobilier_paris_github_actions_deploy -L 3000:127.0.0.1:3000 ubuntu@164.132.42.47
```

Puis ouvrir :

```text
http://localhost:3000
```

Pour une mise en ligne publique propre, il faudra ensuite ajouter un nom de
domaine, HTTPS, et un reverse proxy.

# Livraison continue de l'application

## Objectif

La livraison continue de l'application vérifie que l'application complète peut
être construite et livrée avec Docker.

Elle concerne :

- l'API FastAPI ;
- l'interface Streamlit ;
- la base PostgreSQL ;
- Prometheus ;
- Grafana.

## Fichiers de livraison

Les fichiers utilisés sont :

- `Dockerfile.api` : construit l'image Docker de l'API FastAPI ;
- `Dockerfile.streamlit` : construit l'image Docker de l'interface Streamlit ;
- `compose.yml` : lance l'application localement avec build Docker ;
- `compose.prod.yml` : lance l'application avec des images publiées dans un
  registre Docker ;
- `.github/workflows/livraison-application.yml` : automatise la vérification,
  la construction et la publication des images.

## Fonctionnement sur GitHub

Quand le code est envoyé sur `main`, GitHub Actions :

1. récupère le projet ;
2. vérifie la configuration `compose.yml` ;
3. vérifie la configuration `compose.prod.yml` ;
4. construit l'image Docker de l'API ;
5. construit l'image Docker de Streamlit ;
6. publie les images dans GitHub Container Registry.

Lors d'une pull request, GitHub construit les images pour vérifier que la
livraison est possible, mais ne publie pas les images.

## Images produites

Les images publiées sont :

```text
ghcr.io/<proprietaire>/immobilier-paris-api:latest
ghcr.io/<proprietaire>/immobilier-paris-api:<commit>
ghcr.io/<proprietaire>/immobilier-paris-streamlit:latest
ghcr.io/<proprietaire>/immobilier-paris-streamlit:<commit>
```

Le tag `latest` représente la dernière version validée sur `main`.
Le tag `<commit>` permet de retrouver précisément la version du code utilisée.

## Lancer l'application avec les images publiees

Sur une machine de livraison, définir les variables d'environnement puis lancer :

```bash
export IMAGE_OWNER=<proprietaire-github>
export IMAGE_TAG=latest
docker compose -f compose.prod.yml pull
docker compose -f compose.prod.yml up -d
```

## Mise a jour automatique sur serveur

Le workflow contient un job de déploiement optionnel nommé `deployer-serveur`.
Il est désactivé par défaut.

Pour l'activer, il faut créer la variable GitHub :

```text
DEPLOY_APPLICATION=true
```

Il faut aussi configurer les secrets GitHub :

- `DEPLOY_HOST` ;
- `DEPLOY_USER` ;
- `DEPLOY_SSH_KEY` ;
- `DEPLOY_PATH`.

Quand ces éléments sont configurés, le job se connecte au serveur et exécute :

```bash
docker compose -f compose.prod.yml pull api streamlit
docker compose -f compose.prod.yml up -d
```

Cela met à jour les conteneurs Docker de l'API et de Streamlit avec les images
publiées par GitHub Actions.

Sans serveur configuré, la chaîne publie les images Docker mais ne déclenche pas
le déploiement automatique.

## Correspondance avec C19

- Les fichiers Docker préparent le packaging de l'application.
- GitHub Actions vérifie que la configuration Docker est valide.
- GitHub Actions construit les images API et Streamlit.
- Sur `main`, GitHub Actions publie les images versionnées dans un registre.
- Si un serveur est configuré, GitHub Actions peut mettre à jour les conteneurs
  Docker avec les nouvelles images.

Cela montre que l'application peut être livrée de manière continue et
reproductible.

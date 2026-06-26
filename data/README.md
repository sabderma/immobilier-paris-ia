# Organisation des donnees

Ce dossier suit une convention simple pour eviter de melanger les etapes.

## `raw/`

Donnees brutes collectees depuis les sources externes.

- `raw/scraping/` : CSV bruts produits par chaque scraper immobilier.
- `raw/api/` : JSON bruts produits par les collectes API REST.
- `raw/DVF/` : fichiers DVF bruts par annee, verifies ou telecharges par
  `src/collecte/collecte_dvf.py`.
- `raw/collecte/` : rapports et logs d'execution du pipeline de collecte.

Ces fichiers sont des preuves de collecte et peuvent etre regeneres par les
scripts de `src/collecte/`.

## `processed/`

Donnees intermediaires apres fusion, nettoyage partiel, encodage ou preparation.

Ces fichiers servent de transition entre la collecte brute et les donnees finales.

## `final/`

Donnees propres et stables utilisees par l'application, l'API, le modele ou le
deploiement.

- `annonces_scraping_nettoyees_golden.csv` : annonces immobilieres nettoyees.
- `dvf_paris_clean_2021_2025.csv` : ventes DVF nettoyees.
- `commerces_paris_secours.json` : snapshot final de secours utilise par l'API
  quand la source Open Data Ile-de-France est indisponible.
  Il est genere automatiquement depuis `raw/api/commerces_paris_open_data.json`
  par `src/collecte/preparer_commerces_secours.py`.

## Pourquoi `raw/api` et `final` peuvent contenir des donnees commerces ?

Les deux fichiers n'ont pas le meme role.

- `data/raw/api/commerces_paris_open_data.json` est la reponse brute collectee
  depuis l'API REST. Elle sert de preuve de collecte C1.
- `data/final/commerces_paris_secours.json` est un fichier final de secours,
  embarque dans l'image Docker API, pour maintenir l'application disponible si
  l'API externe ne repond pas. Il est genere automatiquement a partir du fichier
  brut `raw/api`.

Le premier prouve la collecte. Le second sert au fonctionnement de production.

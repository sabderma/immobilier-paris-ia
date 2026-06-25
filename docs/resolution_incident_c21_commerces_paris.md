# C21 - Resolution de l'incident `/commerces/paris`

## Objectif

Ce document prouve la resolution d'un incident technique applicatif, conformement
a la competence C21 : identifier la cause, reproduire le probleme, documenter le
debogage, implementer une correction et valider le retour au fonctionnement
operationnel.

## Incident constate

Date d'analyse : 25 juin 2026.

Sur l'application en ligne, la page **Analyser votre endroit** affichait :

```text
Erreur API sur /commerces/paris :
HTTPConnectionPool(host='api', port=8000): Read timed out. (read timeout=60)
```

Dans Grafana, le dashboard C20 montrait en meme temps :

- API et PostgreSQL disponibles ;
- erreurs 5xx visibles sur la periode observee ;
- latence elevee autour de la route concernee ;
- aucune exception applicative non geree.

L'incident ne venait donc pas d'une API completement arretee, mais d'une route
qui restait bloquee trop longtemps avant de repondre.

Apres une premiere correction, l'erreur bloquante a disparu, mais une regression
fonctionnelle restait visible : le message suivant s'affichait et la notation de
l'arrondissement n'etait plus disponible.

```text
Les statistiques commerces par arrondissement sont temporairement indisponibles.
L'analyse d'adresse exacte reste disponible.
```

Ce second constat a montre que la route repondait bien, mais qu'elle ne
fournissait plus de donnees exploitables lorsque Open Data Ile-de-France et le
cache serveur etaient indisponibles.

## Reproduction

Depuis l'interface :

1. Ouvrir l'application en ligne.
2. Aller sur **Analyser votre endroit**.
3. Constater le message d'erreur Streamlit sur `/commerces/paris`.
4. Apres le premier correctif, constater que le bloc **Noter votre
   arrondissement** reste absent quand la route retourne `data = []`.

Depuis le diagnostic technique, l'appel a la source externe utilisee par la route
a aussi ete teste :

```bash
curl -L --max-time 12 \
  "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/les-commerces-par-commune-ou-arrondissement-base-permanente-des-equipements/records?where=departement%3D75&limit=20&order_by=departement_commune"
```

Resultat observe :

```text
curl: (28) Connection timed out after 12004 milliseconds
HTTP_STATUS:000
TIME_TOTAL:12.004988
```

Cette reproduction confirme que la dependance Open Data pouvait ne pas repondre
dans un delai acceptable.

## Cause racine

La route FastAPI `/commerces/paris` appelait directement l'API Open Data
Ile-de-France au moment de servir la requete utilisateur.

Avant correction :

- le premier appel utilisateur dependait de la disponibilite du service externe ;
- si le service externe ralentissait, la route API restait bloquee ;
- Streamlit attendait l'API interne jusqu'a son timeout de 60 secondes ;
- l'utilisateur voyait une erreur bloquante sur la page.

La cause principale est donc une absence de degradation controlee quand la
dependance externe `data.iledefrance.fr` devient lente ou indisponible.

La cause de la regression restante etait plus precise :

- le fallback sans cache retournait une liste vide ;
- l'interface ne pouvait donc plus construire le tableau des 20 arrondissements ;
- la notation d'arrondissement dependait encore indirectement de la source
  externe au moment de l'affichage ;
- l'image Docker API ne contenait pas de jeu local de secours pour garantir le
  fonctionnement hors ligne de cette fonctionnalite.

## Solution implementee

Fichiers modifies :

- `.dockerignore`
- `.gitignore`
- `Dockerfile.api`
- `api/services/commerces.py`
- `api/routers/location.py`
- `data/final/commerces_paris_secours.json`
- `streamlit/frontend/views/location_rating.py`
- `tests/test_api.py`

Corrections apportees :

- ajout d'un timeout court et configurable pour l'appel Open Data
  (`COMMERCES_API_TIMEOUT_SECONDS`, 5 secondes par defaut) ;
- journalisation explicite de l'indisponibilite externe avec l'evenement
  `commerces_open_data_unavailable` ;
- sauvegarde d'un cache disque local quand l'appel Open Data reussit ;
- reutilisation du cache local si la source Open Data ne repond plus ;
- cache memoire avec TTL court en cas d'echec pour eviter de solliciter la
  dependance externe a chaque affichage de page ;
- retour d'une liste vide controlee si aucune donnee ni cache ne sont
  disponibles, au lieu de bloquer puis produire une erreur 5xx ;
- ajout d'un snapshot local de secours contenant les 20 arrondissements de Paris
  pour restaurer la notation meme quand la source externe est indisponible ;
- copie explicite de ce snapshot dans l'image Docker API ;
- exceptions `.gitignore` et `.dockerignore` pour versionner et embarquer ce
  fichier de secours ;
- tracabilite de l'origine des donnees avec `source_donnees = "open_data"`,
  `"cache_local"` ou `"snapshot_local"` ;
- ajout du champ `source_etat` dans la reponse API pour rendre l'etat de la
  source explicite ;
- adaptation de l'interface Streamlit pour garder l'analyse d'adresse exacte
  disponible meme si les statistiques commerces par arrondissement sont
  temporairement indisponibles.

## Validation

Tests automatises ajoutes :

- timeout de l'Open Data sans cache : `/commerces/paris` retourne `200`,
  `source_etat = "disponible"` et les 20 arrondissements depuis le snapshot
  local ;
- absence totale de source, testee en neutralisant aussi le snapshot :
  `/commerces/paris` retourne `200`, `source_etat = "indisponible"` et
  `data = []` ;
- timeout de l'Open Data avec cache local : `/commerces/paris` retourne les
  donnees du cache avec `source_donnees = "cache_local"`.

Commande executee :

```bash
python3 -m unittest discover -s tests -p test_api.py -k commerces
```

Resultat :

```text
Ran 4 tests in 0.019s
OK
```

Suite complete executee :

```bash
python3 -m unittest discover -s tests
```

Resultat :

```text
Ran 81 tests in 0.482s
OK
```

Le comportement attendu apres deploiement est le suivant :

- la page **Analyser votre endroit** ne doit plus afficher l'erreur
  `Read timed out` sur `/commerces/paris` ;
- le bloc **Noter votre arrondissement** doit rester disponible, meme si
  Open Data Ile-de-France ne repond pas ;
- la route API doit repondre rapidement, meme si Open Data Ile-de-France est
  lent ou indisponible ;
- Grafana doit montrer une baisse des 5xx sur `/commerces/paris` et une latence
  P95 inferieure au seuil d'alerte C20 ;
- les logs doivent contenir un avertissement explicite si la source externe est
  indisponible, puis l'utilisation du snapshot local si aucun cache n'est
  disponible.

## Versionnement attendu

Pour finaliser la preuve C21, la correction doit etre versionnee dans Git avec
les fichiers ci-dessus, puis integree via la chaine de livraison continue.

Exemple de message de commit :

```text
fix: rendre /commerces/paris resilient aux timeouts Open Data
```

Apres push ou merge request, GitHub Actions doit relancer les tests applicatifs
et reconstruire les images Docker API et Streamlit avant de deployer la version
corrigee en ligne.

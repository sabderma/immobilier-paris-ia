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

## Deroule complet de resolution

### 1. Observation du symptome

Le premier signal est venu de l'application en ligne : la page
**Analyser votre endroit** affichait une erreur Streamlit sur la route
`/commerces/paris`.

Le message visible indiquait que Streamlit attendait l'API interne jusqu'a son
timeout de 60 secondes :

```text
HTTPConnectionPool(host='api', port=8000): Read timed out. (read timeout=60)
```

En parallele, Grafana montrait que l'API et PostgreSQL etaient disponibles. Le
probleme etait donc localise sur une route applicative lente, pas sur un arret
global de l'application.

### 2. Reproduction technique

La route `/commerces/paris` a ete analysee cote code. Elle recuperait les
statistiques de commerces via une API externe Open Data Ile-de-France.

L'appel direct a cette source externe avec `curl --max-time 12` a reproduit un
timeout. Cela a permis d'isoler la dependance externe comme facteur declencheur
de l'incident.

### 3. Premiere correction

La premiere correction a transforme l'erreur bloquante en degradation controlee.
L'objectif etait que la route FastAPI reponde vite, meme quand Open Data
Ile-de-France ne repond pas.

Cette correction a ajoute :

- un timeout court cote API ;
- un cache disque local ;
- un cache memoire avec TTL ;
- une reponse controlee en cas d'indisponibilite ;
- des logs explicites pour le diagnostic.

Apres deploiement, le message rouge `Read timed out` avait disparu.

### 4. Regression fonctionnelle detectee

Une deuxieme verification utilisateur a montre que le bloc
**Noter votre arrondissement** ne s'affichait toujours pas. L'erreur technique
avait ete absorbee, mais la route retournait `data = []` lorsque Open Data et le
cache etaient indisponibles.

Cette situation ne produisait plus de 5xx, mais elle empechait toujours la
fonction attendue par l'utilisateur.

### 5. Deuxieme correction

La deuxieme correction a ajoute un snapshot local de secours contenant les 20
arrondissements de Paris. Ce fichier permet a l'application de continuer a
afficher la notation d'arrondissement, meme si la source Open Data est lente ou
indisponible et meme si aucun cache serveur n'existe encore.

Le snapshot est versionne dans Git et copie dans l'image Docker API.

### 6. Validation et livraison

Les tests automatises ont ete lances localement, puis les changements ont ete
pousses sur GitHub. Les Pull Requests ont declenche GitHub Actions, avec tests,
build Docker et deploiement serveur.

La verification finale a ete faite directement sur le VPS avec un appel interne
a `/commerces/paris`. La reponse de production contenait :

```json
{
  "source_etat": "disponible",
  "nombre_resultats": 20,
  "source_donnees": "snapshot_local"
}
```

Le retour utilisateur a confirme que la page fonctionne sur le site en ligne.

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

## Details techniques de la correction

### `api/services/commerces.py`

Le coeur de la correction est dans le service `commerces`.

Techniques ajoutees :

- lecture robuste des variables d'environnement avec `lire_float_env()` pour
  configurer les timeouts et les TTL sans modifier le code ;
- `requests.get(..., timeout=charger_timeout_commerces())` pour eviter qu'un
  appel externe bloque la route FastAPI ;
- `charger_cache_disque_commerces()` pour relire les dernieres donnees valides
  stockees localement ;
- `sauvegarder_cache_disque_commerces()` pour ecrire le cache quand Open Data
  repond correctement ;
- `charger_snapshot_local_commerces()` pour charger le fichier de secours
  `data/final/commerces_paris_secours.json` ;
- variable `_CACHE_COMMERCES` et date `_CACHE_COMMERCES_EXPIRE_AT` pour eviter
  de recalculer ou rappeler la source externe a chaque affichage Streamlit ;
- champ `source_donnees` ajoute a chaque arrondissement pour tracer l'origine
  des donnees : `open_data`, `cache_local` ou `snapshot_local`.

La strategie de fallback est maintenant :

1. essayer Open Data Ile-de-France ;
2. si Open Data echoue, utiliser le cache disque ;
3. si le cache n'existe pas, utiliser le snapshot local ;
4. si aucune source n'existe, retourner une liste vide controlee.

Ce choix evite les erreurs 5xx et preserve la fonctionnalite principale.

### `api/routers/location.py`

La route `/commerces/paris` expose maintenant `source_etat`.

Si la liste des commerces contient des donnees, `source_etat` vaut
`disponible`. Si toutes les sources echouent, il vaut `indisponible`.

Ce champ permet a l'interface et au diagnostic de distinguer :

- une route API fonctionnelle avec donnees disponibles ;
- une route API fonctionnelle mais sans source exploitable.

### `streamlit/frontend/views/location_rating.py`

L'ecran **Analyser votre endroit** ne bloque plus toute la page lorsque les
donnees d'arrondissement sont indisponibles.

La logique est la suivante :

- si le `DataFrame` commerces contient des lignes, afficher le bloc
  **Noter votre arrondissement** ;
- sinon afficher un message d'information ;
- dans les deux cas, conserver l'analyse d'adresse exacte disponible.

Apres l'ajout du snapshot local, le `DataFrame` contient de nouveau les 20
arrondissements en production, donc le bloc de notation redevient visible.

### `Dockerfile.api`, `.dockerignore` et `.gitignore`

Une erreur possible etait de corriger localement sans embarquer le fichier de
secours dans l'image Docker.

Pour eviter cela :

- `.gitignore` autorise explicitement
  `data/final/commerces_paris_secours.json` ;
- `.dockerignore` autorise aussi ce fichier dans le contexte de build Docker ;
- `Dockerfile.api` copie le snapshot dans l'image API avec :

```dockerfile
COPY data/final/commerces_paris_secours.json ./data/final/commerces_paris_secours.json
```

Cette partie garantit que la correction fonctionne aussi apres deploiement, pas
seulement dans le dossier local.

### `tests/test_api.py`

Les tests automatises couvrent les scenarios critiques :

- retour normal d'un arrondissement normalise ;
- timeout Open Data avec snapshot local disponible ;
- timeout Open Data avec cache local disponible ;
- timeout Open Data sans cache et sans snapshot ;
- calcul des scores d'arrondissement.

Les tests utilisent `patch.object()` pour simuler les timeouts et remplacer les
chemins de cache/snapshot par des fichiers temporaires. Cela permet de tester la
logique de fallback sans dependre du reseau.

## Ce que j'ai fait concretement dans le code

1. J'ai identifie que `/commerces/paris` dependait d'un appel externe lent.
2. J'ai ajoute un timeout applicatif court pour eviter le blocage de FastAPI.
3. J'ai ajoute un cache disque pour reutiliser la derniere reponse valide.
4. J'ai ajoute un cache memoire TTL pour reduire les appels repetes.
5. J'ai ajoute des logs de diagnostic quand Open Data est indisponible.
6. J'ai ajoute `source_etat` dans la reponse API.
7. J'ai adapte Streamlit pour ne pas bloquer l'analyse d'adresse exacte.
8. J'ai ajoute un snapshot local des 20 arrondissements.
9. J'ai modifie Docker pour embarquer ce snapshot dans l'image API.
10. J'ai ajoute des tests de timeout, cache et fallback.
11. J'ai pousse les corrections sur GitHub.
12. J'ai verifie les GitHub Actions.
13. J'ai merge les Pull Requests.
14. J'ai attendu le deploiement serveur.
15. J'ai verifie la route en production par SSH et `curl`.

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

## Versionnement et deploiement realises

La correction a ete versionnee et livree en deux etapes :

- PR #1 : correction du timeout et degradation controlee de `/commerces/paris` ;
- PR #2 : ajout du snapshot local pour restaurer la notation d'arrondissement.

Pull Requests :

- `https://github.com/sabderma/immobilier-paris-ia/pull/1`
- `https://github.com/sabderma/immobilier-paris-ia/pull/2`

GitHub Actions a valide :

- les tests applicatifs ;
- la validation du modele IA ;
- la construction des images Docker API et Streamlit ;
- le deploiement serveur.

Verification de production :

- conteneurs API et Streamlit recrees sur le VPS ;
- `/commerces/paris` retourne `200` ;
- `source_etat = "disponible"` ;
- `nombre_resultats = 20` ;
- les donnees proviennent du fallback `snapshot_local` lorsque Open Data est
  indisponible.

## Statut final de la competence C21

La competence C21 est complete et defendable devant le jury.

Le dossier contient :

- l'incident initial ;
- les symptomes visibles ;
- la reproduction ;
- la cause racine ;
- les techniques de debogage ;
- les changements de code ;
- les tests automatises ;
- le versionnement GitHub ;
- la livraison continue ;
- la verification en production.

Le jury reste le seul decisionnaire officiel, mais le projet contient maintenant
une preuve complete de resolution d'incident technique du debut jusqu'a la fin.

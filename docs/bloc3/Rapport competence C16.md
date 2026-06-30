# Rapport competence C16 - Coordination agile du projet

## 1. Objectif de la competence

La competence C16 demande de montrer que j'ai organise la realisation technique
de mon application avec une methode agile.

Dans mon projet, j'ai utilise une organisation Scrum simplifiee avec Jira.

Le but de ce document est d'expliquer simplement :

- comment j'ai decoupe mon projet ;
- comment j'ai cree le backlog ;
- comment j'ai organise les sprints ;
- comment j'ai suivi l'avancement ;
- comment j'ai gere les bugs et les changements ;
- quelles preuves Jira je peux montrer au jury.

Je ne parle pas ici du detail du code. Le code est explique dans les autres
competences. Ici, je parle surtout de l'organisation du travail.

## 2. Projet concerne

Le projet s'appelle :

`immobilier-paris-ia`

C'est une application qui aide a analyser le marche immobilier a Paris.

Elle permet notamment de :

- consulter des donnees DVF ;
- comparer des ventes reelles avec des annonces ;
- afficher des cartes et des graphiques ;
- predire un prix avec un modele IA XGBoost ;
- analyser une adresse avec les transports et services proches ;
- utiliser une interface Streamlit ;
- passer par une API FastAPI ;
- stocker les donnees dans PostgreSQL ;
- lancer l'application avec Docker ;
- suivre l'application avec Prometheus et Grafana.

## 3. Periode du projet

Pour Jira, j'ai retenu la periode reelle de mon projet.

| Element | Valeur |
|---|---|
| Date de debut | 1 mai 2026 |
| Date de fin | 28 juin 2026 |
| Methode | Scrum simplifie |
| Outil | Jira |
| Nom du projet Jira | Immobilier Paris IA |
| Cle Jira | IPI |

Dans Jira, j'ai represente le travail fait pendant cette periode, avec les
epics, les taches, les bugs, les sous-taches et les sprints.

## 4. Pourquoi j'ai choisi Scrum simplifie

J'ai choisi une methode Scrum simplifiee parce que mon projet avait plusieurs
parties differentes a realiser.

Il fallait avancer sur :

- les donnees ;
- la base de donnees ;
- le modele IA ;
- l'API ;
- l'interface ;
- l'authentification ;
- les tests ;
- la livraison ;
- le monitoring.

Sans decoupage, le projet aurait ete difficile a suivre. Avec Jira, j'ai pu
organiser le travail par grands blocs et par sprints.

Comme j'etais seul sur le projet, je n'ai pas fait une methode Scrum complete
comme dans une grande equipe. J'ai adapte la methode a mon cas :

- je faisais la planification moi-meme ;
- je suivais les taches dans Jira ;
- je validais les livrables a la fin de chaque sprint ;
- je gardais une trace des bugs et des corrections ;
- je suivais l'avancement avec les statuts Jira.

## 5. Etape 1 - Cadrage du projet

Avant de creer les tickets Jira, j'ai d'abord cadre le projet.

Cette etape m'a permis de savoir ce que l'application devait faire.

Les questions principales etaient :

- quel probleme je veux resoudre ;
- quelles donnees je dois utiliser ;
- quelles fonctionnalites sont prioritaires ;
- quelles parties techniques sont necessaires ;
- quels livrables doivent etre termines a la fin du projet.

Le besoin principal etait d'aider un utilisateur a mieux comprendre le marche
immobilier parisien.

L'application devait donc regrouper plusieurs informations :

- les ventes reelles DVF ;
- les annonces immobilieres ;
- le prix au metre carre ;
- les arrondissements ;
- l'environnement d'une adresse ;
- une estimation de prix avec IA.

Cette premiere etape m'a aide a creer ensuite les epics dans Jira.

## 6. Etape 2 - Creation des epics

Dans Jira, j'ai cree 11 epics.

Un epic correspond a un grand bloc de travail du projet.

J'ai choisi les epics a partir des vraies parties de mon application.

| Cle Jira | Epic | Periode |
|---|---|---|
| IPI-1 | Collecte des sources de donnees immobilieres | 01/05/2026 - 07/05/2026 |
| IPI-2 | Nettoyage et preparation des donnees | 05/05/2026 - 14/05/2026 |
| IPI-3 | Stockage PostgreSQL et modele de donnees | 10/05/2026 - 19/05/2026 |
| IPI-4 | Analyse du marche et visualisations | 15/05/2026 - 24/05/2026 |
| IPI-5 | Modele IA de prediction du prix | 20/05/2026 - 03/06/2026 |
| IPI-6 | API FastAPI et services metier | 27/05/2026 - 10/06/2026 |
| IPI-7 | Analyse d'adresse et resume IA OpenAI | 01/06/2026 - 14/06/2026 |
| IPI-8 | Interface Streamlit et parcours utilisateur | 05/06/2026 - 18/06/2026 |
| IPI-9 | Authentification, historiques et administration | 10/06/2026 - 20/06/2026 |
| IPI-10 | Tests automatises et integration continue | 14/06/2026 - 24/06/2026 |
| IPI-11 | Livraison, monitoring et stabilisation | 20/06/2026 - 28/06/2026 |

Chaque epic a une date de debut, une date de fin, une description et des
criteres d'acceptation.

Comme je suis seul sur le projet, tous les epics sont assignes a mon compte Jira.

## 7. Couleurs des epics

J'ai aussi ajoute des couleurs aux epics.

Le but est de rendre le backlog plus facile a lire.

| Epic | Couleur Jira |
|---|---|
| IPI-1 | blue |
| IPI-2 | teal |
| IPI-3 | dark_purple |
| IPI-4 | green |
| IPI-5 | purple |
| IPI-6 | dark_blue |
| IPI-7 | orange |
| IPI-8 | yellow |
| IPI-9 | dark_orange |
| IPI-10 | dark_teal |
| IPI-11 | grey |

Cette organisation visuelle aide a distinguer rapidement les themes :

- les donnees ;
- l'IA ;
- l'API ;
- l'interface ;
- les tests ;
- la livraison.

## 8. Etape 3 - Creation du backlog

Apres les epics, j'ai cree le backlog detaille.

Le backlog contient les tickets qui representent le travail a faire.

J'ai cree plusieurs types de tickets :

- des stories ;
- des taches ;
- des bugs ;
- des sous-taches.

Dans Jira, le backlog contient :

| Type | Nombre |
|---|---:|
| Stories | 20 |
| Taches | 23 |
| Bugs | 8 |
| Sous-taches | 102 |
| Total hors epics | 153 |

Avec les 11 epics, le projet contient donc 164 tickets dans Jira.

## 9. Pourquoi j'ai ajoute des bugs

J'ai ajoute des bugs dans Jira parce qu'un vrai projet ne contient pas seulement
des taches normales.

Pendant le projet, il y a eu des points a corriger ou a securiser, par exemple :

- des anomalies dans les donnees scrapees ;
- des valeurs invalides pour la prediction ;
- une carte trop lourde a charger ;
- des routes anciennes a nettoyer ;
- des problemes de validation dans les tests ;
- des erreurs possibles avec les services externes.

Ces bugs montrent que j'ai suivi aussi les problemes techniques, pas seulement
les nouvelles fonctionnalites.

## 10. Exemple de decoupage d'un epic

Exemple avec l'epic de prediction IA.

Epic :

`IPI-5 - Modele IA de prediction du prix`

Tickets lies a cet epic :

- preparer les variables du modele IA ;
- comparer plusieurs modeles ;
- entrainer le modele XGBoost final ;
- produire les metriques ;
- corriger les entrees invalides de prediction.

Les sous-taches permettent ensuite de detailler le travail.

Par exemple, pour le modele XGBoost :

- construire le pipeline ;
- entrainer le modele ;
- sauvegarder le fichier `.joblib` ;
- verifier les metriques ;
- tester une prediction.

Ce decoupage m'a permis de rendre le travail plus clair.

## 11. Etape 4 - Organisation des sprints

J'ai cree 5 sprints dans Jira.

Les sprints couvrent toute la periode du projet.

| Sprint | Dates | Objectif | Tickets parents |
|---|---|---|---:|
| IPI S1 - Donnees | 1 mai - 10 mai | Collecter les sources DVF, scraping et commerces. | 4 |
| IPI S2 - Nettoyage | 11 mai - 24 mai | Nettoyer les donnees et structurer PostgreSQL. | 12 |
| IPI S3 - Marche IA | 25 mai - 7 juin | Travailler sur l'analyse marche, l'IA et l'API. | 8 |
| IPI S4 - Interface | 8 juin - 20 juin | Finaliser l'interface, l'adresse et les comptes utilisateurs. | 19 |
| IPI S5 - Livraison | 21 juin - 28 juin | Stabiliser avec les tests, Docker, CI/CD et monitoring. | 8 |

Les sous-taches restent rattachees a leurs tickets parents.

## 12. Logique des sprints

J'ai organise les sprints dans un ordre logique.

Au debut, j'avais besoin des donnees.

Ensuite, j'ai nettoye les donnees et prepare la base.

Apres cela, j'ai pu travailler sur l'analyse et le modele IA.

Ensuite, j'ai developpe l'interface et les fonctions utilisateur.

Enfin, j'ai termine avec les tests, la livraison, Docker et le monitoring.

Cette organisation suit la logique technique du projet :

1. recuperer les donnees ;
2. nettoyer et stocker ;
3. analyser et predire ;
4. rendre utilisable dans une interface ;
5. tester et livrer.

## 13. Etape 5 - Suivi des statuts

Dans Jira, les tickets passent par plusieurs statuts.

Le workflow utilise est :

| Statut | Signification |
|---|---|
| A faire | Le ticket est prevu mais pas encore commence. |
| En cours | Le ticket est en train d'etre traite. |
| Revue en cours | Le ticket doit etre verifie. |
| Termine | Le ticket est fini. |

Pour representer le projet fini, les tickets sont passes en `Termine`.

J'ai fait attention a ne pas seulement mettre les tickets en termine directement.
J'ai aussi demarre et cloture les sprints dans Jira pour garder une trace agile
plus correcte.

## 14. Etat final des sprints

Dans Jira, l'etat final est le suivant :

| Sprint | Etat Jira | Tickets |
|---|---|---:|
| IPI S1 - Donnees | Cloture | 4 |
| IPI S2 - Nettoyage | Cloture | 12 |
| IPI S3 - Marche IA | Cloture | 8 |
| IPI S4 - Interface | Cloture | 19 |
| IPI S5 - Livraison | Actif pour affichage du tableau | 8 |

Les sprints 1 a 4 sont clotures.

Le sprint 5 est laisse actif dans Jira pour pouvoir afficher le tableau final
avec les tickets dans la colonne `Termine`.

Tous les tickets du projet sont termines.

## 15. Rituels agiles adaptes

Comme j'etais seul, les rituels agiles ont ete adaptes.

Je n'ai pas fait de reunions avec une equipe, mais j'ai garde la logique des
rituels.

| Rituel | Application dans mon projet |
|---|---|
| Sprint planning | Choisir les tickets du sprint selon les priorites et les dates. |
| Daily suivi | Verifier ce qui est fait, ce qui bloque et ce qu'il faut faire ensuite. |
| Sprint review | Verifier les livrables a la fin du sprint. |
| Retrospective | Noter ce qu'il faut ameliorer pour le sprint suivant. |

Cette adaptation est coherente avec mon projet, car j'etais le seul
developpeur.

## 16. Suivi des changements

Pendant le projet, certains elements ont evolue.

J'ai utilise Jira pour garder une trace des changements importants.

Exemples :

| Changement ou probleme | Reponse dans le projet |
|---|---|
| Donnees de scraping parfois irregulieres | Ajout de nettoyage et de controles. |
| Carte avec beaucoup de points | Optimisation et chargement a la demande. |
| Prediction avec valeurs invalides | Ajout de validations Pydantic. |
| Services externes parfois indisponibles | Ajout de fallback ou gestion d'erreur. |
| Besoin d'authentification | Ajout de comptes, JWT, roles et historiques. |
| Besoin de surveillance | Ajout de `/health`, `/metrics`, Prometheus et Grafana. |

Ces changements ont ete lies a des taches ou bugs Jira.

## 17. Communication de l'avancement

Jira permet de communiquer l'avancement du projet.

Dans mon cas, les informations visibles sont :

- les epics ;
- les tickets ;
- les sous-taches ;
- les dates ;
- les sprints ;
- les statuts ;
- les story points ;
- les bugs ;
- le burndown.

Meme si j'etais seul, cette organisation permet a un jury ou a une autre
personne de comprendre comment le projet a avance.

## 18. Outils de pilotage utilises

Les outils de pilotage utilises pour cette competence sont :

| Outil | Utilisation |
|---|---|
| Jira | Backlog, epics, sprints, tickets, bugs et burndown. |
| Tableau Scrum | Voir les tickets du sprint actif. |
| Backlog Jira | Organiser les tickets avant les sprints. |
| Graphique Burndown | Suivre les story points restants. |
| Git / GitHub | Garder le code versionne. |
| GitHub Actions | Lancer les tests et la livraison. |

Pour C16, l'outil principal reste Jira.

## 19. Rapports Jira

Dans Jira, j'ai retrouve le rapport suivant :

`Graphique Burndown du sprint`

Il est disponible dans :

`Rapports > More reports > Graphique Burndown du sprint`

Ce rapport montre :

- le sprint selectionne ;
- les dates du sprint ;
- l'objectif du sprint ;
- le champ d'estimation en story points ;
- le travail restant ;
- le journal des changements de perimetre.

Pour mon rapport final, ce graphique sera une preuve importante de la methode
Scrum.

## 20. Preuves a ajouter au rapport final

Pour completer ce document avec des preuves visuelles, je prevois d'ajouter des
captures Jira.

Les captures importantes sont :

| Capture | Ce qu'elle prouve |
|---|---|
| Backlog avec les epics | Le projet est decoupe en grands blocs. |
| Liste des tickets | Le backlog contient stories, taches, bugs et sous-taches. |
| Tableau Scrum du sprint 5 | Les tickets du dernier sprint sont termines. |
| Graphique Burndown | Le suivi Scrum est disponible dans Jira. |
| Vue rapports Jira | Les tickets sont bien termines et classes par type. |

Ces captures seront ajoutees dans le rapport final.

## 21. Lien avec les livrables du projet

Les epics Jira correspondent aux vrais fichiers et livrables du projet.

| Partie Jira | Exemples de preuves dans le projet |
|---|---|
| Donnees | `src/collecte/`, `data/final/` |
| Nettoyage | `src/nettoyage/` |
| Base PostgreSQL | `sql/`, `src/database/` |
| IA | `src/prediction/`, `models/`, `livraison/` |
| API | `api/main.py`, `api/routers/`, `api/services/` |
| Interface | `streamlit/frontend/` |
| Authentification | `api/routers/auth.py`, `api/services/auth.py` |
| Tests | `tests/` |
| CI/CD | `.github/workflows/` |
| Livraison | `Dockerfile.api`, `Dockerfile.streamlit`, `compose.yml` |
| Monitoring | `monitoring/`, `api/metrics.py` |

Cela montre que Jira n'est pas separe du projet. Les tickets correspondent bien
a ce qui a ete developpe.

## 22. Ce que cette competence montre

Avec cette competence C16, je montre que j'ai su organiser mon projet avec une
methode agile.

Je montre aussi que je sais :

- decouper un projet en epics ;
- transformer les epics en tickets ;
- organiser le travail en sprints ;
- suivre l'avancement ;
- ajouter des bugs quand il y a des problemes ;
- utiliser un tableau Scrum ;
- utiliser un rapport Burndown ;
- relier les tickets aux livrables techniques.

Cette competence ne montre pas seulement que j'ai code une application.

Elle montre aussi que j'ai su organiser le travail pour arriver a une version
complete et testable.

## 23. Conclusion

Pour mon projet `immobilier-paris-ia`, j'ai utilise Jira avec une methode Scrum
simplifiee.

J'ai cree :

- 11 epics ;
- 153 tickets de backlog, dont 102 sous-taches ;
- 5 sprints ;
- 8 bugs ;
- un suivi avec les statuts Jira ;
- un graphique Burndown.

Le projet est organise sur la periode du 1 mai 2026 au 28 juin 2026.

Les sprints permettent de comprendre l'ordre du travail, depuis la collecte des
donnees jusqu'a la livraison et au monitoring.

Pour moi, la competence C16 est donc couverte, car Jira montre bien la
coordination technique du projet avec une conduite agile.

# Audit du projet par rapport au référentiel Développeur en intelligence artificielle

Date de l'audit : 10 juin 2026

Projet audité : `immobilier-paris-ia`

Référentiel analysé : Référentiel d'activités, de compétences et d'évaluation
« Développeur en intelligence artificielle », 25 pages, titre 2023.

## Conclusion importante

Le PDF fourni est un référentiel général. Il ne contient aucun résultat personnel,
aucune note, aucune coche et aucune mention « validé » ou « non validé ».

Il est donc impossible de confirmer les compétences officiellement validées par
le jury à partir de ce PDF. Seul un relevé de résultats, un procès-verbal de jury
ou une attestation de blocs permettrait de connaître les validations officielles.

Le présent rapport évalue plutôt la capacité actuelle du projet à démontrer les
compétences devant un jury.

## Légende de l'audit

- **SOLIDE** : preuves techniques importantes présentes et fonctionnelles. La
  compétence paraît défendable, mais le jury reste seul décisionnaire.
- **PARTIEL** : une partie significative existe, mais plusieurs critères
  obligatoires ou preuves écrites manquent.
- **NON DÉMONTRÉ** : aucune preuve suffisante n'a été trouvée dans le dépôt.

## Résumé général

| Niveau de preuve | Nombre | Compétences |
|---|---:|---|
| SOLIDE | 7 | C2, C3, C5, C9, C10, C11, C12 |
| PARTIEL | 9 | C1, C4, C8, C13, C15, C17, C18, C19, C20 |
| NON DÉMONTRÉ | 5 | C6, C7, C14, C16, C21 |

Cette estimation ne signifie pas « 7 compétences officiellement validées ».
Elle signifie que 7 compétences disposent déjà de preuves techniques fortes.

## Vérifications réellement effectuées

- Les 25 pages du référentiel ont été lues et les compétences C1 à C21 ont été
  comparées au dépôt.
- Les tests automatisés ont été exécutés le 10 juin 2026 :
  **22 tests exécutés, 22 réussis**.
- La configuration Docker Compose a été vérifiée avec `docker compose config` :
  **configuration valide**.
- Le dépôt Git distant existe sur GitHub.
- Plusieurs éléments importants sont encore non suivis ou modifiés localement,
  notamment les Dockerfiles, `compose.yml`, Grafana et le script d'import Docker.
  Tant qu'ils ne sont pas commités et poussés, ils ne prouvent pas le critère
  « sources versionnées et accessibles depuis un dépôt Git distant ».

## Risque principal pour le jury

Le projet contient beaucoup plus de travail technique que de preuves écrites.
Les fichiers suivants sont actuellement vides :

- `README.md`
- `docs/presentation_projet.md`
- `docs/rgpd.md`
- `docs/specifications_fonctionnelles.md`
- `docs/specifications_techniques.md`
- `docs/competences_rncp.md`

Un jury peut considérer une compétence comme non démontrée même si le code existe,
si le rapport professionnel n'explique pas les choix, les procédures, les tests,
les contraintes et les résultats.

# Bloc 1 - Collecte, stockage et mise à disposition des données

Évaluation prévue par le référentiel :

- **E1 - Mise en situation couvrant C1 à C5**
- Rapport professionnel individuel
- Correction du rapport
- Soutenance orale individuelle

## C1 - Automatiser l'extraction de données

**État : PARTIEL**

### Preuves présentes

- Cinq scripts de scraping Selenium :
  `src/collecte/scrappcentury21.py`, `scrappforet.py`, `scrapplefigaro.py`,
  `scrapporpi.py` et `scrappstephaneplazaimmobilier.py`.
- Données brutes provenant de plusieurs sites immobiliers.
- Lecture de fichiers CSV DVF et de fichiers de scraping.
- Appels à des API externes dans l'application, notamment l'API des commerces.
- Scripts versionnés dans Git.

### Ce qui manque ou reste fragile

- `src/collecte/collecte_api.py` et `src/collecte/collecte_csv.py` sont vides.
- Aucun script clair ne télécharge automatiquement les fichiers DVF.
- Aucune collecte démontrée depuis un système big data.
- Aucun script unique et documenté ne lance toute la collecte.
- La gestion des erreurs, reprises, logs et exceptions des scrapers est inégale.
- Les contraintes légales, règles de confidentialité et conditions d'utilisation
  des sites scrapés ne sont pas documentées.
- Les spécifications techniques de collecte sont absentes.

### À faire pour sécuriser la validation

1. Développer un vrai script de collecte API et un script de téléchargement DVF.
2. Créer une commande unique orchestrant toutes les collectes.
3. Ajouter logs, gestion des erreurs, délais, reprise et rapport de collecte.
4. Documenter les sources, contraintes, formats et règles d'utilisation.
5. Expliquer l'absence de big data ou ajouter une démonstration minimale.

## C2 - Développer des requêtes SQL d'extraction

**État : SOLIDE**

### Preuves présentes

- `sql/requetes_analyse_DVF.sql` contient des requêtes d'analyse et de contrôle.
- `sql/requetes_analyse_scraping.sql` contient des sélections, contrôles et
  suppressions documentées.
- `api/core.py` construit des requêtes filtrées et paramétrées.
- Les routes FastAPI interrogent PostgreSQL pour fournir les données.
- `docs/documentation_sql.md` explique le rôle des scripts SQL.

### Ce qui reste à améliorer

- Expliquer davantage les choix de filtrage, les performances et les index.
- Ajouter des exemples d'exécution et de résultats.
- Documenter les optimisations appliquées aux requêtes.
- Ajouter des requêtes ou une justification concernant le big data.

## C3 - Développer les règles d'agrégation et de nettoyage

**État : SOLIDE**

### Preuves présentes

- Fusion de cinq sources de scraping dans
  `src/nettoyage/fusion_sources_scraping.py`.
- Nettoyage, normalisation des formats et suppression des doublons.
- Pipeline source, master et golden pour les annonces.
- Nettoyage et fusion des données DVF de 2021 à 2025.
- Contrôles SQL des anomalies.
- Données finales générées pour l'analyse et l'entraînement.

### Ce qui reste à améliorer

- Ajouter une documentation technique complète du pipeline.
- Décrire les dépendances, commandes et ordre exact d'exécution.
- Justifier précisément chaque seuil de nettoyage.
- Transformer les scripts exécutés au chargement en fonctions réutilisables.
- Ajouter des tests automatisés exécutés par la CI pour tout le nettoyage.

## C4 - Créer une base de données dans le respect du RGPD

**État : PARTIEL**

### Preuves présentes

- Base PostgreSQL définie dans `sql/creation_tables.sql`.
- Tables source, master, golden et DVF.
- Scripts d'import avec pandas et SQLAlchemy.
- Import Docker automatisé pour DVF.
- Variables sensibles chargées depuis l'environnement.

### Ce qui manque

- Aucun modèle conceptuel de données Merise.
- Aucun modèle physique présenté sous forme de diagramme.
- `docs/rgpd.md` est vide.
- Aucun registre des traitements de données personnelles.
- Aucune procédure de tri, durée de conservation ou suppression RGPD.
- La procédure d'installation et d'import n'est pas complètement documentée.
- Le projet contient des adresses DVF : leur traitement doit être analysé et
  justifié dans le document RGPD.

### À faire pour sécuriser la validation

1. Créer MCD et MPD.
2. Compléter `docs/rgpd.md` avec finalité, base légale, données, destinataires,
   durée de conservation, sécurité et droits des personnes.
3. Créer un registre de traitement.
4. Définir et démontrer une procédure de tri ou suppression.
5. Documenter l'installation et les imports PostgreSQL.

## C5 - Développer une API REST mettant les données à disposition

**État : SOLIDE**

### Preuves présentes

- API REST FastAPI structurée en routes, services et schémas.
- Routes DVF, statistiques, export CSV, commerces et filtres.
- Authentification par en-tête `X-API-Key`.
- Comparaison sécurisée de la clé avec `compare_digest`.
- Validation des entrées avec les schémas FastAPI.
- Documentation OpenAPI générée automatiquement par FastAPI.
- Tests de sécurité et de routes dans `tests/test_api.py`.
- Les tests de l'API réussissent localement.

### Ce qui reste à améliorer

- Rédiger une documentation API destinée au jury : architecture, routes,
  paramètres, réponses, erreurs, authentification et exemples.
- Documenter explicitement les mesures OWASP.
- Ajouter limitation de débit, journalisation et stratégie de rotation des clés.
- Ajouter les tests API à la CI.

# Bloc 2 - Intégrer des modèles et services d'intelligence artificielle

Évaluations prévues :

- **E2 - Cas pratique couvrant C6 à C8**
- **E3 - Mise en situation couvrant C9 à C13**
- Rapports professionnels individuels
- Soutenances orales individuelles avec démonstration pour E3

## C6 - Organiser et réaliser une veille technique et réglementaire

**État : NON DÉMONTRÉ**

### Preuves présentes

- Aucune preuve structurée trouvée.

### Ce qui manque

- Thématique de veille.
- Planning récurrent d'au moins une heure par semaine.
- Outil d'agrégation des sources.
- Critères de fiabilité des sources.
- Synthèses datées.
- Partage des synthèses aux parties prenantes.
- Veille sur accessibilité, sécurité, données et réglementation.

### À faire

Créer un dossier `docs/veille/` avec planning, liste de sources qualifiées,
synthèses datées et recommandations appliquées au projet.

## C7 - Identifier et recommander des services d'IA préexistants

**État : NON DÉMONTRÉ**

### Preuves présentes

- Le projet compare Random Forest et XGBoost.
- Le projet utilise Gemini avec plusieurs modèles de repli.

### Pourquoi cela ne suffit pas

Le référentiel demande un benchmark formalisé de services d'IA préexistants,
avec besoins, contraintes, solutions étudiées et écartées, avantages,
inconvénients, prérequis et démarche écoresponsable. Aucun document de ce type
n'a été trouvé.

### À faire

Créer un benchmark comparant au minimum plusieurs solutions pour la notation
d'adresse ou la prédiction immobilière : Gemini, autre service externe,
modèle local et option sans IA externe.

## C8 - Paramétrer un service d'intelligence artificielle

**État : PARTIEL**

### Preuves présentes

- Intégration du service Gemini dans `api/services/address.py`.
- Configuration par variables d'environnement.
- Gestion de plusieurs modèles de repli.
- Tests des erreurs temporaires et définitives.
- Intégration dans une route API et dans Streamlit.

### Ce qui manque

- Documentation d'installation et de configuration de Gemini.
- Documentation des accès, droits, dépendances et données envoyées.
- Analyse RGPD des adresses envoyées à un service tiers.
- Monitoring spécifique du service Gemini.
- Preuve d'accessibilité de la documentation.

## C9 - Développer une API REST exposant un modèle d'IA

**État : SOLIDE**

### Preuves présentes

- Route `POST /prediction/prix`.
- Chargement et exécution du modèle XGBoost.
- Validation des paramètres et réponse structurée.
- Authentification par clé API.
- Métriques de durée, erreur et nombre de prédictions.
- Tests automatisés de la route et de l'authentification.
- Sources suivies dans le dépôt distant.
- OpenAPI généré par FastAPI.

### Ce qui reste à améliorer

- Documenter explicitement l'architecture et les règles OWASP.
- Ajouter davantage de tests de validation des entrées invalides.
- Ajouter les tests API à la CI.
- Fournir des captures ou résultats d'une démonstration complète.

## C10 - Intégrer l'API d'un modèle ou service d'IA dans une application

**État : SOLIDE**

### Preuves présentes

- L'application Streamlit appelle l'API FastAPI.
- Le formulaire de prédiction appelle `/prediction/prix`.
- L'application appelle également la fonctionnalité Gemini de notation.
- La clé API est transmise par l'application.
- Gestion des erreurs HTTP et réseau.
- Interfaces adaptées à la prédiction et à la notation d'adresse.
- Sources versionnées.

### Ce qui reste à améliorer

- Ajouter des tests automatisés de l'intégration Streamlit vers l'API.
- Réaliser et documenter un audit d'accessibilité.
- Documenter la correspondance entre besoins, routes et interfaces.

## C11 - Monitorer un modèle d'intelligence artificielle

**État : SOLIDE**

### Preuves présentes

- Métriques Prometheus spécifiques au modèle.
- Suivi du volume, de la durée, des erreurs et des prix prédits.
- Exposition des métriques de qualité MAE, RMSE et R2.
- Configuration Prometheus.
- Dashboard Grafana détaillé.
- Documentation dans `docs/monitoring_modele.md`.
- Services Prometheus et Grafana intégrés à Docker Compose.

### Ce qui reste à améliorer

- Démarrer toute la chaîne et conserver des captures ou preuves d'exécution.
- Configurer des alertes opérationnelles.
- Définir les déclencheurs éventuels de réentraînement.
- Documenter maintenance, installation et utilisation plus complètement.
- Commiter et pousser les fichiers Grafana et Docker actuellement locaux.

## C12 - Programmer les tests automatisés d'un modèle d'IA

**État : SOLIDE**

### Preuves présentes

- Tests de nettoyage des données d'entraînement.
- Tests du format d'entrée du modèle.
- Test d'entraînement produisant modèle et métriques.
- Test de prédiction positive.
- Seuil automatique de qualité `R2 >= 0.80`.
- Tests exécutés avec succès : 22 tests du projet réussis.
- Tests du modèle intégrés à GitHub Actions.

### Ce qui reste à améliorer

- Documenter le plan de tests et la stratégie de couverture.
- Calculer et publier la couverture.
- Ajouter des tests de dérive, de données extrêmes et de reproductibilité.
- Versionner les données avec un outil adapté ou documenter leur gestion.

## C13 - Créer une chaîne de livraison continue d'un modèle d'IA

**État : PARTIEL**

### Preuves présentes

- Workflow GitHub Actions `livraison-modele.yml`.
- Déclenchement sur push vers `main` et manuellement.
- Installation des dépendances.
- Exécution des tests du modèle.
- Livraison du modèle et des métriques sous forme d'artifact.

### Ce qui manque

- Aucun test de données intégré à la chaîne.
- Aucune étape d'entraînement dans la chaîne.
- Aucune étape d'évaluation générant un rapport dans la chaîne.
- Aucune validation automatique d'un seuil avant livraison.
- Aucun packaging Docker ou déploiement intégré au workflow.
- Aucune procédure d'installation, test, déclenchement ou débogage de la chaîne.

# Bloc 3 - Réaliser une application intégrant un service d'IA

Évaluations prévues :

- **E4 - Mise en situation couvrant C14 à C19**
- **E5 - Cas pratique couvrant C20 et C21**
- Rapport professionnel et démonstration pour E4
- Documentation de monitoring et résolution d'incident pour E5

## C14 - Analyser le besoin d'application

**État : NON DÉMONTRÉ**

### Preuves présentes

- L'application permet de cartographier, analyser et prédire l'immobilier
  parisien, ce qui laisse comprendre le besoin général.

### Ce qui manque

- `docs/specifications_fonctionnelles.md` est vide.
- Aucun MCD ou diagramme entités-relations.
- Aucun parcours utilisateur ou wireframe.
- Aucune user story avec critères d'acceptation.
- Aucun objectif d'accessibilité WCAG ou RGAA.

### À faire

Rédiger les spécifications fonctionnelles complètes avec personas, parcours,
user stories, critères d'acceptation, wireframes et exigences d'accessibilité.

## C15 - Concevoir le cadre technique de l'application

**État : PARTIEL**

### Preuves présentes

- Architecture réelle en couches : Streamlit, FastAPI, PostgreSQL, modèle,
  Prometheus et Grafana.
- Dockerfiles et Docker Compose.
- Services externes Gemini et API commerces.
- Application fonctionnelle et structurée.

### Ce qui manque

- `docs/specifications_techniques.md` est vide.
- Aucun diagramme d'architecture.
- Aucun diagramme de flux de données.
- Aucune justification des choix techniques et écoresponsables.
- Aucune conclusion formelle de preuve de concept.
- Les fichiers Docker actuels ne sont pas encore suivis dans Git.

## C16 - Coordonner la réalisation technique dans une conduite agile

**État : NON DÉMONTRÉ**

### Preuves présentes

- Historique Git présent.

### Ce qui manque

- Méthode agile choisie et expliquée.
- Backlog, tableau Kanban ou autre outil de pilotage.
- Sprints ou cycles documentés.
- Rôles, rituels et comptes rendus.
- Communication d'avancement, imprévus et décisions.

### À faire

Créer et conserver un backlog, un tableau de suivi et des comptes rendus courts
de cycles ou rituels. Relier les tâches aux commits et aux livrables.

## C17 - Développer les composants et interfaces de l'application

**État : PARTIEL**

### Preuves présentes

- Application Streamlit complète avec carte, tableau, filtres, graphiques,
  prédiction, notation d'adresse et présentation des sources.
- API FastAPI structurée.
- Validation des formulaires et schémas.
- Accès aux données PostgreSQL.
- Protection des routes par clé API.
- Tests unitaires et d'intégration API.
- Sources versionnées sur GitHub.

### Ce qui manque

- Maquettes initiales permettant de prouver la conformité des interfaces.
- Audit et critères d'accessibilité.
- Documentation des mesures OWASP.
- Tests automatisés propres à l'interface Streamlit.
- Analyse d'écoconception.
- Documentation technique complète d'installation et d'architecture.

## C18 - Automatiser les tests du code source avec une CI

**État : PARTIEL**

### Preuves présentes

- GitHub Actions est configuré.
- Les tests du modèle sont exécutés automatiquement sur `main`.
- La configuration est versionnée sur le dépôt distant.

### Ce qui manque

- Les tests API ne sont pas exécutés par la CI.
- Aucun lint, formatage, contrôle de sécurité ou couverture.
- Aucun test de l'application Streamlit.
- Aucune documentation de la CI.
- La CI ne couvre donc pas encore l'ensemble de l'application.

## C19 - Créer un processus de livraison continue de l'application

**État : PARTIEL**

### Preuves présentes

- Deux Dockerfiles existent.
- Docker Compose package PostgreSQL, API, Streamlit, Prometheus et Grafana.
- La configuration Docker Compose est syntaxiquement valide.

### Ce qui manque

- Les Dockerfiles, Compose et Grafana ne sont pas encore commités et poussés.
- Aucun build Docker dans GitHub Actions.
- Aucun déploiement automatique en test ou préproduction.
- Aucune étape de livraison après validation.
- Aucune documentation de la procédure de livraison et de débogage.

## C20 - Surveiller une application d'intelligence artificielle

**État : PARTIEL**

### Preuves présentes

- Prometheus et Grafana sont configurés.
- Le dashboard contient des seuils visuels.
- L'API expose des métriques Python et des métriques du modèle.
- Docker Compose intègre les outils de monitoring.

### Ce qui manque

- Monitoring dédié aux routes et à la santé globale de l'application.
- Journalisation structurée de l'API et de Streamlit.
- Alertes réellement configurées et testées.
- Seuils d'alerte documentés pour chaque risque.
- Procédures complètes d'installation et de configuration.
- Analyse RGPD des logs.
- Preuve de fonctionnement de la chaîne complète.

## C21 - Résoudre et documenter un incident technique

**État : NON DÉMONTRÉ**

### Preuves présentes

- L'historique Git montre des évolutions et corrections, mais aucun dossier
  d'incident complet n'a été trouvé.

### Ce qui manque

- Incident choisi et clairement décrit.
- Message d'erreur ou symptôme initial.
- Étapes de reproduction.
- Recherche de la cause racine.
- Procédure de débogage.
- Solution testée.
- Preuve du commit ou de la pull request corrigeant l'incident.

### À faire

Documenter un incident réel déjà rencontré, par exemple une erreur de modèle,
de connexion PostgreSQL, de route API ou d'intégration Gemini, avec toutes les
étapes de reproduction, diagnostic, correction et validation.

# Priorités recommandées

## Priorité 1 - Éviter les blocages immédiats du jury

1. Compléter les six documents vides.
2. Créer un rapport professionnel reliant explicitement C1 à C21 aux preuves.
3. Commiter et pousser Docker, Compose, Grafana et les modifications locales.
4. Ajouter les tests API à GitHub Actions.
5. Préparer une démonstration reproductible de bout en bout.

## Priorité 2 - Couvrir les compétences actuellement non démontrées

1. C6 : créer la veille technique et réglementaire.
2. C7 : rédiger le benchmark de services d'IA.
3. C14 : rédiger besoins, parcours, user stories et accessibilité.
4. C16 : fournir les preuves de gestion agile.
5. C21 : rédiger un dossier complet de résolution d'incident.

## Priorité 3 - Transformer les compétences partielles en preuves solides

1. C1 : automatiser et documenter toute la collecte.
2. C4 : produire MCD, MPD, registre RGPD et procédure de tri.
3. C8 : documenter et monitorer le service Gemini.
4. C13 : compléter la chaîne MLOps.
5. C15 : documenter architecture et flux.
6. C17 : ajouter accessibilité, sécurité et tests d'interface.
7. C18 et C19 : créer une vraie CI/CD de l'application.
8. C20 : ajouter logs, alertes et procédure de monitoring.

# Réponse directe à « qu'est-ce que j'ai validé ? »

À partir des fichiers fournis, aucune validation officielle ne peut être
confirmée. En revanche, le projet démontre déjà fortement :

- SQL et extraction de données : C2
- Agrégation et nettoyage : C3
- API REST de données : C5
- API exposant le modèle : C9
- Intégration de l'API dans l'application : C10
- Monitoring du modèle : C11
- Tests automatisés du modèle : C12

Les autres compétences sont soit partielles, soit non encore démontrées dans
les livrables actuels. Le plus gros travail restant n'est pas uniquement du
développement : c'est la production de preuves structurées pour le jury.

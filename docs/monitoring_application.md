# Monitoring applicatif - C20

## Objectif

Ce document décrit le monitoring de l'application complète `Immobilier Paris IA`.
Il complète le monitoring du modèle XGBoost documenté dans
`docs/monitoring_modele.md`.

La compétence C20 porte sur la surveillance de l'application d'intelligence
artificielle dans son ensemble : disponibilité de l'API, santé de la base de
données, erreurs HTTP, latence des routes, journalisation et alertes.

## Différence entre C11 et C20

| Compétence | Périmètre | Métriques principales |
|---|---|---|
| C11 | Modèle IA XGBoost | `model_predictions_total`, `model_prediction_duration_seconds`, `model_prediction_errors_total`, `model_evaluation_mae_euros` |
| C20 | Application IA complète | `api_http_requests_total`, `api_http_request_duration_seconds`, `api_database_health_status`, `api_exceptions_total` |

## Outillage

- FastAPI expose les métriques sur la route `/metrics`.
- Prometheus collecte les métriques toutes les 5 secondes.
- Grafana affiche deux dashboards séparés :
  - `C11 - Monitoring modele IA` ;
  - `C20 - Monitoring application`.
- Prometheus charge les règles d'alerte depuis `monitoring/alerts.yml`.

## Métriques applicatives surveillées

| Métrique | Description | Utilité |
|---|---|---|
| `up{job="immobilier-paris-api"}` | Disponibilité du endpoint `/metrics` | Détecter une API indisponible |
| `api_database_health_status` | Etat de connexion PostgreSQL : `1` OK, `0` KO | Détecter une base inaccessible |
| `api_http_requests_total` | Nombre de requêtes par méthode, route et statut HTTP | Suivre l'activité et les erreurs |
| `api_http_request_duration_seconds` | Durée des requêtes HTTP par route | Détecter les ralentissements |
| `api_http_requests_in_progress` | Nombre de requêtes en cours | Identifier une saturation |
| `api_exceptions_total` | Nombre d'exceptions non gérées | Détecter les incidents applicatifs |

Les métriques `api_*` sont alimentées automatiquement par un middleware FastAPI
dans `api/main.py`. La route `/metrics` est exclue des compteurs HTTP pour éviter
que le scraping Prometheus ne pollue les statistiques applicatives.

## Seuils d'alerte

| Risque | Alerte Prometheus | Seuil | Gravité |
|---|---|---:|---|
| API indisponible | `ApiIndisponible` | `up == 0` pendant 1 minute | Critique |
| Base PostgreSQL indisponible | `BaseDonneesIndisponible` | `api_database_health_status == 0` pendant 1 minute | Critique |
| Erreurs HTTP trop nombreuses | `TauxErreursHttpEleve` | Plus de 5 % de réponses 5xx sur 5 minutes pendant 2 minutes | Warning |
| Latence élevée | `LatenceHttpP95Elevee` | P95 supérieur à 2 secondes pendant 2 minutes | Warning |

Ces seuils sont volontairement simples pour un environnement local ou de
préproduction. En production, ils seraient ajustés après observation du trafic
réel.

## Journalisation

L'API produit des logs structurés JSON via `api/logging_config.py`.

Chaque requête journalisée contient :

- l'événement (`api_request_completed` ou `api_request_failed`) ;
- la méthode HTTP ;
- la route FastAPI ;
- le code HTTP ;
- la durée en millisecondes ;
- l'adresse IP cliente.

Les logs ne contiennent pas le corps des requêtes, pas de clé API, pas de mot de
passe et pas de token JWT. Cette règle limite l'exposition de données
personnelles ou sensibles.

## Analyse RGPD des logs

Les logs peuvent contenir une adresse IP cliente, qui est une donnée personnelle.
Les mesures suivantes sont appliquées :

- aucune donnée métier issue des formulaires n'est écrite dans les logs ;
- les secrets applicatifs ne sont jamais journalisés ;
- les logs servent uniquement au diagnostic technique et à la sécurité ;
- en production, une durée de conservation limitée doit être définie selon la
  politique de l'organisation ;
- l'accès aux logs doit être réservé aux personnes chargées de l'exploitation et
  du support technique.

## Procédure d'installation

Depuis la racine du projet :

```bash
docker compose up -d --build
```

Services utiles :

- API : `http://127.0.0.1:8002`
- métriques Prometheus exposées par l'API : `http://127.0.0.1:8002/metrics`
- Prometheus : `http://127.0.0.1:9090`
- Grafana : `http://127.0.0.1:3000`

Dans Grafana, ouvrir le dossier `Immobilier Paris`, puis le dashboard
`C20 - Monitoring application`.

## Vérifications manuelles

1. Appeler `http://127.0.0.1:8002/health` et vérifier la réponse
   `{"status":"ok","database":"connectée"}`.
2. Appeler quelques routes API ou utiliser l'interface Streamlit.
3. Ouvrir `http://127.0.0.1:8002/metrics` et vérifier la présence des métriques
   `api_http_requests_total`, `api_http_request_duration_seconds` et
   `api_database_health_status`.
4. Dans Prometheus, ouvrir `Status > Rules` et vérifier que les règles du groupe
   `immobilier-paris-application` sont chargées.
5. Dans Grafana, vérifier que le dashboard `C20 - Monitoring application`
   affiche la disponibilité de l'API, la santé PostgreSQL, les codes HTTP et la
   latence.

## Preuves de fichiers

- Métriques applicatives : `api/metrics.py`
- Middleware HTTP et logs : `api/main.py`
- Santé PostgreSQL et endpoint `/metrics` : `api/routers/system.py`
- Configuration Prometheus : `monitoring/prometheus.yml`
- Règles d'alerte : `monitoring/alerts.yml`
- Dashboard Grafana C20 : `monitoring/grafana/dashboards/immobilier-paris-application.json`
- Orchestration Docker : `compose.yml`

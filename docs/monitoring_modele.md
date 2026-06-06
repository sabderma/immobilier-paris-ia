# Monitoring du modèle d’intelligence artificielle

## Objectif

L’objectif est de surveiller le modèle de prédiction immobilière utilisé dans le projet afin de vérifier son bon fonctionnement après son intégration dans l’application.

Le modèle surveillé est le modèle XGBoost qui prédit le prix d’un bien immobilier à Paris.

## Modèle concerné

- Nom du modèle : XGBRegressor
- Fichier du modèle : models/xgboost_prix_dvf.joblib
- Type de modèle : modèle de régression
- Objectif : prédire le prix estimé d’un appartement à Paris
- Route API concernée : POST /prediction/prix

## Outils choisis

Pour surveiller le modèle, les outils choisis sont :

- Prometheus : collecte les métriques du modèle
- Grafana : affiche les métriques dans un tableau de bord
- FastAPI : expose les métriques via une route /metrics

## Pourquoi Prometheus et Grafana ?

Prometheus permet de récupérer automatiquement les métriques exposées par l’API.
Grafana permet de visualiser ces métriques dans un dashboard clair.

Ces outils permettent de suivre l’utilisation du modèle, de détecter les erreurs et d’identifier des comportements anormaux.


## Métriques surveillées

Pour valider le monitoring du modèle, plusieurs métriques sont suivies.

| Métrique | Description | Utilité |
|---|---|---|
| model_predictions_total | Nombre total de prédictions réalisées par le modèle | Vérifier l’utilisation du modèle |
| model_prediction_duration_seconds | Temps nécessaire pour réaliser une prédiction | Détecter un modèle trop lent |
| model_prediction_errors_total | Nombre d’erreurs pendant les prédictions | Détecter les problèmes techniques |
| model_predicted_price_euros | Prix estimé retourné par le modèle | Surveiller les valeurs prédites |
| model_predictions_by_arrondissement_total | Nombre de prédictions par arrondissement | Analyser les zones les plus demandées |
| model_evaluation_mae_euros | Erreur moyenne absolue calculée sur les ventes de test | Mesurer la précision réelle du modèle |
| model_evaluation_rmse_euros | Erreur donnant plus d’importance aux grandes erreurs | Détecter les prédictions très éloignées du prix réel |
| model_evaluation_r2_score | Part de la variation des prix expliquée par le modèle | Évaluer la qualité globale du modèle |
| model_evaluation_test_samples | Nombre de ventes utilisées pour l’évaluation | Vérifier que l’évaluation repose sur suffisamment de données |

## Pourquoi ces métriques sont importantes ?

Ces métriques permettent de vérifier que le modèle fonctionne correctement après son intégration dans l’application.

Elles permettent notamment de répondre aux questions suivantes :

- Le modèle est-il utilisé ?
- Le modèle répond-il rapidement ?
- Le modèle génère-t-il des erreurs ?
- Les prix estimés sont-ils cohérents ?
- Certains arrondissements sont-ils plus demandés que d’autres ?

## Erreur moyenne du modèle

L'erreur moyenne du modèle est calculée pendant l'entraînement sur les données de
test, qui représentent 20 % des ventes DVF disponibles. Elle ne dépend pas des
prédictions réalisées par les utilisateurs.

Le résultat actuel est une MAE de 111 078,36 euros sur 30 487 ventes de test.
Cela signifie qu'en moyenne, l'écart absolu entre le prix prédit et le véritable
prix de vente est d'environ 111 078 euros.

Cette valeur est enregistrée dans `models/xgboost_prix_dvf_metrics.json`, puis
exposée par l'API dans la métrique Prometheus `model_evaluation_mae_euros`.

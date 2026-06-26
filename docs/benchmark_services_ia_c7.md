# C7 - Benchmark et recommandation de services d'IA

## Objectif de la competence

Cette preuve montre que plusieurs solutions d'intelligence artificielle ont ete
identifiees, comparees puis recommandees selon le besoin du projet
`immobilier-paris-ia`.

Le besoin principal du projet est double :

- estimer le prix d'un appartement parisien a partir de donnees DVF ;
- generer un resume lisible du secteur a partir des donnees de proximite
  affichees dans l'application.

## Solutions comparees

| Solution | Usage possible | Avantages | Limites | Decision |
|---|---|---|---|---|
| Modele local XGBoost | Prediction du prix immobilier | Performant sur donnees tabulaires, deployable dans Docker, pas d'envoi des donnees utilisateur a un service externe | Necessite entrainement, suivi des metriques et livraison du modele | Retenu pour la prediction |
| Random Forest local | Prediction du prix immobilier | Robuste, simple a expliquer, bon modele de comparaison | Moins performant dans le benchmark du projet | Ecarte au profit de XGBoost |
| Service IA externe de type AutoML/API cloud | Prediction du prix immobilier | Moins de maintenance modele, infrastructure geree | Cout, dependance fournisseur, confidentialite des donnees, reproductibilite plus faible | Non retenu pour la prediction |
| OpenAI API | Resume textuel du secteur | Generation de texte claire a partir de donnees structurees, integration rapide | Service externe, cout variable, besoin de limiter les donnees envoyees | Retenu uniquement pour le resume optionnel |
| Option sans IA generative | Resume du secteur par phrases fixes | Pas de cout externe, pas de dependance API | Texte moins naturel, moins adaptable aux donnees de proximite | Garde-fou possible si OpenAI indisponible |

## Benchmark technique du modele de prediction

Le benchmark local est implemente dans
`src/prediction/comparaison_modeles_prix.py`.

Techniques utilisees :

- nettoyage des donnees DVF et suppression des valeurs invalides ;
- selection des variables `surface_reelle_bati`, `nombre_pieces_principales`
  et `arrondissement` ;
- separation entrainement/test avec `train_test_split(test_size=0.2,
  random_state=42)` ;
- encodage de l'arrondissement avec `OneHotEncoder(handle_unknown="ignore")` ;
- pipeline scikit-learn combinant preprocessing et modele ;
- comparaison de `RandomForestRegressor` et `XGBRegressor` ;
- evaluation avec `MAE`, `RMSE` et `R2` ;
- export des resultats dans `models/comparaison_xgboost_random_forest_prix.json`
  et `models/comparaison_xgboost_random_forest_prix.csv` ;
- suivi MLflow optionnel pour tracer les essais.

Resultats du benchmark :

| Modele | Lignes test | R2 | MAE | RMSE |
|---|---:|---:|---:|---:|
| RandomForestRegressor | 30 487 | 0.8425 | 114 790.87 euros | 205 470.48 euros |
| XGBRegressor | 30 487 | 0.8538 | 111 078.36 euros | 197 974.42 euros |

Le choix retenu est donc `XGBRegressor`, car il obtient le meilleur RMSE et un
MAE plus faible sur le jeu de test.

## Ce qui a ete fait dans le code pour la prediction

Le modele retenu est integre cote API dans `api/services/prediction.py`.

Points techniques :

- le modele est charge depuis `models/xgboost_prix_dvf.joblib` avec `joblib` ;
- le chargement est mis en cache memoire dans la variable `modele_prediction`
  pour eviter de relire le fichier a chaque prediction ;
- l'API verifie aussi la presence des metriques dans
  `models/xgboost_prix_dvf_metrics.json` ;
- la fonction `predire_prix_xgboost()` reconstruit un `DataFrame` avec les memes
  variables que pendant l'entrainement ;
- si le modele ou ses metriques sont absents, l'API renvoie une erreur 503
  explicite au lieu d'un plantage silencieux.

Le modele est expose ensuite par la route de prediction FastAPI et utilise dans
l'ecran Streamlit **Predire appartement**.

## Service IA externe retenu pour le resume de secteur

Pour la generation de texte, le projet utilise OpenAI dans
`api/services/location_summary.py`.

Cette integration est volontairement limitee au resume du secteur. La prediction
de prix reste locale avec XGBoost pour limiter les couts, la dependance externe
et l'envoi de donnees utilisateur.

Ce qui est fait dans le code :

- le modele OpenAI est configurable avec `OPENAI_MODEL`, par defaut
  `gpt-5.4-mini` ;
- l'appel utilise un timeout court (`TIMEOUT_OPENAI_SECONDES = 25`) et
  `max_retries=1` ;
- `store=False` est envoye a l'API OpenAI pour ne pas stocker les donnees de la
  requete ;
- les instructions demandent un resume court, neutre, factuel et interdisent
  d'inventer des informations absentes des donnees ;
- seules les donnees utiles de proximite sont envoyees au modele ;
- si `OPENAI_API_KEY` est absente ou si OpenAI est indisponible, l'application
  retourne une erreur controlee et continue de fonctionner.

Les tests dans `tests/test_api.py` verifient notamment que :

- l'appel OpenAI utilise le modele configure ;
- `store=False` est bien transmis ;
- les coordonnees brutes `latitude` et `longitude` ne sont pas envoyees dans le
  prompt ;
- le resume OpenAI reste optionnel quand la cle API n'est pas configuree.

## Recommandation finale

La recommandation retenue est hybride :

- utiliser un modele local XGBoost pour la prediction immobiliere, car il est
  plus performant que Random Forest dans le benchmark et ne depend pas d'une API
  externe ;
- utiliser OpenAI uniquement pour transformer des donnees deja calculees en
  texte court et comprehensible ;
- conserver des comportements de repli lorsque les services externes ne sont pas
  disponibles.

Cette approche est adaptee au projet, car elle separe clairement :

- le calcul metier critique, execute localement ;
- l'aide redactionnelle, confiee a un service IA externe mais controlee ;
- les donnees publiques ou personnelles, limitees au strict necessaire.

## Demarche responsable

Le choix technique limite l'usage de services externes :

- la prediction ne declenche pas d'appel IA cloud ;
- le resume OpenAI est court avec `max_output_tokens=220` ;
- les donnees envoyees sont reduites aux informations utiles ;
- le modele local est charge une seule fois en memoire ;
- les erreurs externes sont gerees sans bloquer l'application.

## Statut de la competence C7

Avec ce benchmark, les preuves codees, les resultats chiffres et la
recommandation finale, la competence C7 est complete et defendable devant le
jury.

Le jury reste le seul decisionnaire officiel, mais le depot contient maintenant
une preuve structuree et reliee au code.

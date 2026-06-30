# Rapport competence C13 - Livraison continue du modele IA

## 1. Objectif de la competence C13

La competence C13 demande de creer une chaine de livraison continue pour un
modele d'intelligence artificielle.

Dans mon projet, le modele concerne est :

`XGBRegressor`

Il sert a predire le prix d'un appartement a Paris.

Le but de C13 est simple : au lieu de tester, entrainer et livrer le modele a la
main, j'ai une chaine GitHub Actions qui fait les etapes automatiquement.

## 2. Difference entre C12 et C13

| Competence | Explication simple |
|---|---|
| C12 | Je cree les tests du modele IA. |
| C13 | Je cree la chaine automatique qui lance les tests, entraine, valide et livre le modele. |

Donc C12 repond a la question :

`Est-ce que mon modele passe les tests ?`

C13 repond a la question :

`Est-ce que GitHub peut refaire automatiquement la validation et la livraison du modele ?`

## 3. Ce que demande le referentiel

Pour C13, le referentiel demande notamment :

- definir les etapes de la chaine ;
- definir les declencheurs ;
- configurer les variables et les chemins ;
- installer l'environnement ;
- integrer les tests des donnees ;
- integrer les tests du modele ;
- integrer l'entrainement du modele ;
- generer un rapport de resultat ;
- livrer le modele si tout est valide ;
- versionner le fichier de configuration de la chaine ;
- documenter l'installation, la configuration, le lancement et le debug.

Dans mon projet, j'ai utilise GitHub Actions parce que le projet est deja sur
Git et que GitHub Actions peut lancer automatiquement les commandes Python.

## 4. Schema Draw.io de la chaine C13

Le schema de la chaine C13 est dans un fichier separe :

`docs/bloc2/schema_c13_livraison_modele.drawio`

Ce schema precise les tests lances par la chaine.

Pour les donnees, il montre que `test_donnees_livraison.py` verifie :

- le fichier CSV ;
- le volume de donnees ;
- les colonnes obligatoires ;
- les valeurs manquantes ;
- les valeurs positives ;
- les arrondissements de Paris.

Pour le modele, il montre que `test_prediction.py` verifie :

- le nettoyage des lignes invalides ;
- le format de prediction ;
- la creation du modele `.joblib` ;
- la creation des metriques `.json` ;
- une prediction positive ;
- le seuil `R2 >= 0.80` ;
- les champs obligatoires du fichier de metriques.

## 5. Fichier principal de la chaine

Le fichier principal de C13 est :

`.github/workflows/livraison-modele.yml`

C'est ce fichier qui dit a GitHub Actions quoi faire.

Il contient :

- les declencheurs ;
- la version de Python ;
- les variables de chemin ;
- les commandes de test ;
- la commande d'entrainement ;
- la commande de rapport ;
- la livraison sous forme d'artifact.

## 6. Declencheurs de la chaine

La chaine demarre dans trois cas.

| Declencheur | Explication |
|---|---|
| `push` sur `main` | Quand du code est envoye sur la branche principale. |
| `pull_request` vers `main` | Quand une modification est proposee avant fusion. |
| `workflow_dispatch` | Quand je lance la chaine manuellement depuis GitHub. |

J'ai garde ces trois declencheurs car ils couvrent les cas importants :

- verifier automatiquement le modele avant une fusion ;
- valider le modele apres une modification ;
- pouvoir relancer la chaine a la main si besoin.

## 7. Variables de la chaine

Dans le workflow, j'ai defini plusieurs variables.

| Variable | Valeur | Role |
|---|---|---|
| `DONNEES_ENTRAINEMENT` | `data/final/dvf_paris_clean_2021_2025.csv` | Fichier CSV utilise pour entrainer le modele. |
| `DOSSIER_LIVRAISON` | `livraison` | Dossier ou les fichiers livres sont crees. |
| `MODELE_LIVRE` | `livraison/xgboost_prix_dvf.joblib` | Nouveau modele entraine. |
| `METRIQUES_LIVREES` | `livraison/xgboost_prix_dvf_metrics.json` | Scores du nouveau modele. |
| `RAPPORT_LIVRAISON` | `livraison/rapport_livraison_modele.md` | Rapport genere apres validation. |

Ces variables rendent le workflow plus lisible. Au lieu de repeter les chemins
partout, la chaine utilise des noms simples.

## 8. Etapes detaillees de C13

| Etape | Fichier ou commande | Ce que ca fait |
|---|---|---|
| Recuperer le projet | `actions/checkout@v4` | GitHub telecharge le depot. |
| Installer Python | `actions/setup-python@v5` | Installe Python `3.12`. |
| Installer les dependances | `pip install -r requirements.txt` | Installe les bibliotheques Python du projet. |
| Tester les donnees | `python -m unittest discover -s tests -p "test_donnees_livraison.py" -v` | Verifie que les donnees DVF sont valides. |
| Entrainer le modele | `python -m src.prediction.entrainement_xgboost_prix ...` | Cree un nouveau modele XGBoost. |
| Tester le modele | `python -m unittest discover -s tests -p "test_prediction.py" -v` | Verifie que le nouveau modele fonctionne. |
| Generer le rapport | `python scripts/generer_rapport_livraison_modele.py ...` | Cree le rapport et controle le seuil `R2`. |
| Livrer l'artifact | `actions/upload-artifact@v4` | Met le modele, les metriques et le rapport dans une archive GitHub. |

## 9. Tests lances par C13

La chaine lance deux familles de tests.

| Test | Fichier | Ce qu'il verifie |
|---|---|---|
| Test des donnees | `tests/test_donnees_livraison.py` | CSV present, colonnes obligatoires, valeurs positives, arrondissements 1 a 20. |
| Test du modele | `tests/test_prediction.py` | Nettoyage, entrainement, prediction positive, metriques, seuil `R2 >= 0.80`. |

Ces tests viennent de C12. Mais C13 est importante parce qu'elle les relance
automatiquement dans GitHub Actions.

## 10. Entrainement dans la chaine

La chaine lance ce script :

`src/prediction/entrainement_xgboost_prix.py`

La commande utilisee dans GitHub Actions est :

```bash
python -m src.prediction.entrainement_xgboost_prix \
  --input "$DONNEES_ENTRAINEMENT" \
  --output-model "$MODELE_LIVRE" \
  --output-metrics "$METRIQUES_LIVREES"
```

Cette commande cree :

- `livraison/xgboost_prix_dvf.joblib` ;
- `livraison/xgboost_prix_dvf_metrics.json`.

Le modele est entraine a partir du fichier :

`data/final/dvf_paris_clean_2021_2025.csv`

## 11. Validation du seuil R2

Apres les tests, la chaine lance :

`scripts/generer_rapport_livraison_modele.py`

Ce script lit :

`livraison/xgboost_prix_dvf_metrics.json`

Il verifie que :

`R2 >= 0.80`

Si le score est inferieur a `0.80`, la chaine s'arrete avec une erreur.

Dans le modele actuel, le score est :

`R2 = 0.8538`

Donc le modele est accepte.

## 12. Rapport de livraison

La chaine genere ce fichier :

`livraison/rapport_livraison_modele.md`

Ce rapport contient :

- la date de livraison ;
- le nom du modele ;
- le nombre de lignes utilisees ;
- le nombre de lignes d'entrainement ;
- le nombre de lignes de test ;
- le score `R2` ;
- le seuil minimum ;
- la `MAE` ;
- la `RMSE` ;
- la decision finale.

Dans le rapport actuel, la decision est :

`LIVRAISON ACCEPTEE`

## 13. Livraison sous forme d'artifact

Si tout passe, GitHub Actions cree un artifact.

Nom de l'artifact :

`modele-immobilier-paris-valide-<numero_execution>`

Il contient :

- `livraison/xgboost_prix_dvf.joblib` ;
- `livraison/xgboost_prix_dvf_metrics.json` ;
- `livraison/rapport_livraison_modele.md`.

L'artifact est une archive telechargeable depuis GitHub Actions.

Il est garde pendant `30` jours.

## 14. Pourquoi il n'y a pas d'artifact sur une pull request

Dans le workflow, il y a cette condition :

```yaml
if: github.event_name != 'pull_request'
```

Cela veut dire que sur une pull request, la chaine verifie le modele, mais elle
ne livre pas encore l'artifact final.

C'est logique, parce qu'une pull request sert d'abord a verifier avant fusion.
La livraison finale se fait apres un `push` sur `main` ou un lancement manuel.

## 15. Fichiers concernes par C13

| Fichier | Role dans C13 |
|---|---|
| `.github/workflows/livraison-modele.yml` | Fichier principal de la chaine GitHub Actions. |
| `requirements.txt` | Dependances installees par la chaine. |
| `data/final/dvf_paris_clean_2021_2025.csv` | Donnees utilisees pour entrainer le modele. |
| `tests/test_donnees_livraison.py` | Tests des donnees lances par la chaine. |
| `tests/test_prediction.py` | Tests du modele lances par la chaine. |
| `src/prediction/entrainement_xgboost_prix.py` | Script qui entraine le modele dans la chaine. |
| `src/prediction/prediction.py` | Code de prediction teste indirectement par la chaine. |
| `scripts/generer_rapport_livraison_modele.py` | Script qui valide le `R2` et genere le rapport. |
| `livraison/xgboost_prix_dvf.joblib` | Modele produit par la chaine. |
| `livraison/xgboost_prix_dvf_metrics.json` | Metriques produites par la chaine. |
| `livraison/rapport_livraison_modele.md` | Rapport produit par la chaine. |

## 16. Bibliotheques et outils utilises

| Outil | Role |
|---|---|
| GitHub Actions | Execute automatiquement la chaine. |
| `actions/checkout@v4` | Recupere le code du depot. |
| `actions/setup-python@v5` | Installe Python dans l'environnement GitHub. |
| Python `3.12` | Version de Python utilisee dans la chaine. |
| `pip` | Installe les dependances. |
| `unittest` | Lance les tests C12 dans la chaine C13. |
| `xgboost` | Entraine le modele final. |
| `scikit-learn` | Calcule les metriques et prepare le pipeline. |
| `actions/upload-artifact@v4` | Livre le modele, les metriques et le rapport. |

## 17. Comment lancer la chaine

La chaine peut se lancer automatiquement avec un `push` ou une pull request.

Elle peut aussi se lancer manuellement :

1. Aller sur GitHub.
2. Ouvrir l'onglet `Actions`.
3. Choisir `Livraison continue du modele IA`.
4. Cliquer sur `Run workflow`.
5. Choisir la branche.
6. Lancer la chaine.

## 18. Comment verifier que la chaine a marche

Une execution reussie doit montrer :

- etape `Verifier les donnees d'entrainement` en vert ;
- etape `Entrainer un nouveau modele IA` en vert ;
- etape `Tester le nouveau modele IA` en vert ;
- etape `Generer le rapport de livraison` en vert ;
- artifact cree si ce n'est pas une pull request.

Le rapport doit indiquer :

```text
Decision : LIVRAISON ACCEPTEE
```

Verification locale faite le 28 juin 2026 :

| Verification | Resultat |
|---|---|
| Syntaxe du workflow `.github/workflows/livraison-modele.yml` | OK |
| Compilation des fichiers Python utilises par la chaine | OK |
| `test_donnees_livraison.py` | 5 tests executes, OK |
| `test_prediction.py` | 6 tests executes, OK |
| Generation du rapport de livraison | Rapport cree, OK |

## 19. Cas ou la chaine refuse le modele

La chaine peut refuser le modele si :

- le fichier CSV est absent ;
- les donnees ont des colonnes manquantes ;
- les valeurs sont invalides ;
- l'entrainement plante ;
- les tests C12 echouent ;
- le score `R2` est inferieur a `0.80` ;
- les fichiers de livraison ne sont pas crees.

Dans ces cas, GitHub Actions affiche l'etape qui a echoue.

## 20. Versionnement Git

Le fichier de configuration de la chaine est dans Git :

`.github/workflows/livraison-modele.yml`

Commandes de versionnement :

```bash
git add "docs/bloc2/Rapport competence C13.md"
git add "docs/bloc2/schema_c13_livraison_modele.drawio"
git add .github/workflows/livraison-modele.yml
git add src/prediction/entrainement_xgboost_prix.py
git add src/prediction/prediction.py
git add scripts/generer_rapport_livraison_modele.py
git add tests/test_donnees_livraison.py
git add tests/test_prediction.py
git commit -m "docs: ajouter le rapport competence C13"
```

Verification Git :

```bash
git status --short
git ls-files ".github/workflows/livraison-modele.yml"
```

## 21. Limites et ameliorations possibles

La chaine C13 est deja utile, mais elle peut etre amelioree.

Par exemple, les ameliorations possibles sont :

- une publication automatique du modele vers un stockage externe ;
- un lien direct entre l'artifact et l'application en production ;
- une verification de derive des donnees ;
- une notification en cas d'echec ;
- un rapport plus detaille avec graphiques.

Mais pour mon projet, la chaine montre deja les points importants :

- declenchement automatique ;
- installation de l'environnement ;
- tests des donnees ;
- entrainement ;
- tests du modele ;
- validation du seuil ;
- rapport ;
- livraison sous forme d'artifact.

## 22. Conclusion

La competence C13 est couverte parce que le modele IA peut etre valide et livre
avec une chaine automatique GitHub Actions.

La chaine ne livre pas directement un modele au hasard. Elle verifie les donnees,
entraine un nouveau modele, relance les tests, controle le score `R2`, genere un
rapport et livre seulement si tout est correct.

Cela rend la livraison du modele plus propre, plus reproductible et plus fiable.

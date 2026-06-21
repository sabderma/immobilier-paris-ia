# Livraison continue du modèle d'intelligence artificielle

## Objectif

La chaîne de livraison continue vérifie les données, entraîne un nouveau modèle
XGBoost, teste ce nouveau modèle et le livre uniquement si tous les contrôles
réussissent.

La configuration de la chaîne se trouve dans :

```text
.github/workflows/livraison-modele.yml
```

## Pourquoi utiliser GitHub Actions ?

GitHub Actions est un service qui exécute automatiquement des commandes sur
GitHub. Il évite de livrer manuellement un modèle qui ne fonctionne pas ou dont
la qualité est insuffisante.

## Déclencheurs

La chaîne démarre :

- automatiquement après un envoi de code sur la branche `main` ;
- automatiquement lors d'une pull request vers la branche `main`, pour vérifier
  le modèle avant fusion ;
- manuellement depuis l'onglet Actions de GitHub.

## Données utilisées

La chaîne utilise le fichier complet DVF contenant plus de 150 000 ventes :

```text
data/final/dvf_paris_clean_2021_2025.csv
```

Le fichier est stocké dans le dépôt GitHub afin que GitHub Actions puisse
entraîner automatiquement le modèle sur les mêmes données que celles utilisées
localement. Le dépôt étant public, ce fichier DVF public est également
accessible aux visiteurs du dépôt.

## Étapes de la chaîne

### 1. Récupération du projet

GitHub télécharge la dernière version du dépôt.

### 2. Installation de l'environnement

La chaîne installe Python 3.12 et les dépendances de `requirements.txt`.

### 3. Vérification des données

Les tests de `tests/test_donnees_livraison.py` vérifient :

- la présence d'au moins 100 000 ventes ;
- les colonnes obligatoires ;
- l'absence de valeurs obligatoires manquantes ;
- les surfaces, pièces et prix strictement positifs ;
- les arrondissements compris entre 1 et 20 ;
- la représentation des 20 arrondissements.

Si un contrôle échoue, la chaîne s'arrête avant l'entraînement.

Cette étape correspond à la compétence **C12**. La chaîne de livraison continue
de la compétence **C13** exécute automatiquement ces tests C12.

### 4. Entraînement d'un nouveau modèle

La chaîne lance :

```text
src/prediction/entrainement_xgboost_prix.py
```

Elle produit un nouveau modèle et ses nouvelles métriques dans le dossier
temporaire `livraison/`.

### 5. Test du nouveau modèle

Le nouveau modèle remplace temporairement le modèle du dépôt uniquement dans
l'environnement GitHub Actions. Les tests de `tests/test_prediction.py`
contrôlent ensuite :

- la préparation des données ;
- l'entraînement ;
- la création des métriques ;
- la capacité du modèle à produire un prix positif ;
- le respect du seuil de qualité `R² >= 0,80` ;
- la présence des champs obligatoires dans le fichier de métriques.

Si un test échoue, la chaîne s'arrête et aucun modèle n'est livré.

Cette étape correspond aussi à la compétence **C12**. Elle est lancée
automatiquement par la chaîne **C13**.

### 6. Génération du rapport

Le script `scripts/generer_rapport_livraison_modele.py` vérifie une dernière fois
le seuil R² et génère un rapport contenant :

- le nombre de ventes utilisées ;
- le R² ;
- la MAE ;
- la RMSE ;
- la décision de livraison.

### 7. Livraison

Si toutes les étapes réussissent, GitHub crée l'artifact :

```text
modele-immobilier-paris-valide-<numero_execution>
```

L'artifact est créé uniquement lors d'un envoi sur `main` ou lors d'un lancement
manuel. Lors d'une pull request, la chaîne vérifie les données, entraîne et teste
le modèle, mais ne crée pas de livraison finale.

Il contient :

```text
xgboost_prix_dvf.joblib
xgboost_prix_dvf_metrics.json
rapport_livraison_modele.md
```

L'artifact reste téléchargeable pendant 30 jours.
GitHub regroupe automatiquement ces fichiers dans une archive téléchargeable,
ce qui constitue le packaging du modèle validé.

## Cas de refus de livraison

La livraison est automatiquement refusée si :

- les données sont absentes ou invalides ;
- l'entraînement échoue ;
- un test automatisé échoue ;
- le R² du nouveau modèle est inférieur à `0,80` ;
- un fichier attendu pour la livraison est absent.

## Lancer manuellement la chaîne

1. Ouvrir le dépôt sur GitHub.
2. Ouvrir l'onglet **Actions**.
3. Sélectionner **Livraison continue du modele IA**.
4. Cliquer sur **Run workflow**.
5. Sélectionner la branche `main`.
6. Cliquer sur le bouton de lancement.

## Récupérer le modèle livré

1. Ouvrir une exécution réussie dans l'onglet **Actions**.
2. Descendre jusqu'à la section **Artifacts**.
3. Télécharger `modele-immobilier-paris-valide-<numero_execution>`.

## Diagnostiquer un échec

1. Ouvrir l'exécution en erreur dans l'onglet **Actions**.
2. Ouvrir l'étape rouge.
3. Lire le message d'erreur.
4. Corriger les données, le modèle ou les tests concernés.
5. Relancer manuellement la chaîne ou envoyer la correction sur `main`.

## Correspondance avec les compétences

- **C12** : les tests automatisés vérifient les données et le modèle.
- **C13** : GitHub Actions exécute automatiquement les tests C12, entraîne le
  modèle, bloque les mauvaises versions et livre automatiquement une version
  validée.

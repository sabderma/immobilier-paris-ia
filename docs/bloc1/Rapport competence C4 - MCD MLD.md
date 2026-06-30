# Rapport competence C4 - MCD et MLD

## 1. Objectif du document

Ce document complete mon rapport de competence C4.

Le but ici est de montrer comment j'ai reflechi a ma base de donnees avant de
la creer dans PostgreSQL. Je montre donc :

- le **MCD**, qui explique les grandes donnees du projet et les liens entre
  elles ;
- le **MLD**, qui montre les tables plus proches de PostgreSQL ;
- le fichier draw.io que j'ai cree pour avoir un schema propre et modifiable.

Le fichier du schema est stocke ici :

`docs/schema_mcd_mld.drawio`

J'ai choisi draw.io parce que c'est simple a utiliser, visuel, gratuit, et je
peux garder le fichier dans Git avec le reste du projet.

## 2. Difference entre MCD et MLD

Le **MCD** veut dire Modele Conceptuel de Donnees.

Pour moi, le MCD sert a expliquer les objets importants du projet sans penser
tout de suite au code SQL. C'est plus une vue metier. Par exemple, je peux dire
qu'un utilisateur fait des predictions, ou que les annonces passent de source a
master puis golden.

Le **MLD** veut dire Modele Logique de Donnees.

Le MLD est plus proche de la base de donnees. Dans mon cas, il montre les vraies
tables PostgreSQL, les cles primaires, les cles etrangeres et les types de
colonnes importants.

Donc j'ai fait les deux, parce que :

- le MCD montre la logique generale du projet ;
- le MLD montre comment cette logique devient des tables SQL ;
- les deux ensemble rendent la competence C4 plus claire.

## 3. Mon MCD

Dans mon MCD, j'ai mis les objets principaux du projet.

### Utilisateur

L'utilisateur represente une personne qui peut se connecter a l'application.

Il peut :

- lancer des predictions de prix immobilier ;
- rechercher une adresse exacte ;
- avoir un role comme `user`, `admin` ou `super_admin`.

### Prediction

La prediction represente une estimation de prix faite par l'application.

Elle utilise des informations comme :

- la surface ;
- le nombre de pieces ;
- l'arrondissement ;
- le prix predit.

Un utilisateur peut faire plusieurs predictions.

### Historique adresse

Cette partie garde les adresses exactes recherchees par l'utilisateur.

Je stocke :

- l'adresse ;
- la latitude ;
- la longitude ;
- la date de recherche.

C'est utile pour garder une trace des recherches, mais il faut faire attention
car une adresse exacte peut identifier une recherche precise.

### Annonce source

L'annonce source correspond aux donnees brutes qui viennent du scraping.

A ce niveau, les donnees ne sont pas encore vraiment propres. Par exemple, le
prix, la surface ou le nombre de pieces peuvent encore etre en texte.

### Annonce master

L'annonce master est une etape intermediaire.

Elle contient les annonces apres un premier nettoyage. Je garde encore plusieurs
informations de depart, mais elles sont deja mieux organisees.

### Annonce golden

L'annonce golden est la version finale des annonces scraping.

C'est cette table qui est vraiment utile pour les analyses, l'API et les
comparaisons. Les colonnes importantes sont numeriques, comme le prix, la
surface et le prix au m2.

### Vente DVF

La vente DVF represente une vente immobiliere reelle.

Elle vient des donnees DVF et contient :

- la date de mutation ;
- la valeur fonciere ;
- la surface ;
- le nombre de pieces ;
- l'arrondissement ;
- la latitude et la longitude.

Cette table est importante parce qu'elle donne des prix reels, contrairement au
scraping qui donne des prix d'annonces.

## 4. Mon MLD

Dans le MLD, j'ai repris les vraies tables creees dans mes fichiers SQL.

Les fichiers SQL utilises sont :

- `sql/creation_tables.sql`
- `sql/creation_tables_utilisateurs.sql`

### Table `users`

Cette table stocke les comptes utilisateurs.

Colonnes principales :

- `id` : cle primaire ;
- `email` : adresse email de connexion ;
- `password_hash` : mot de passe hache, jamais le mot de passe en clair ;
- `first_name` et `last_name` : nom et prenom ;
- `role` : role de l'utilisateur ;
- `is_active` : indique si le compte est actif ;
- `created_at` et `updated_at` : dates de creation et modification.

J'ai aussi un index unique sur l'email pour eviter deux comptes avec le meme
email.

### Table `predictions`

Cette table stocke les predictions faites par les utilisateurs.

Colonnes principales :

- `id` : cle primaire ;
- `user_id` : cle etrangere vers `users(id)` ;
- `surface` ;
- `nb_pieces` ;
- `arrondissement` ;
- `predicted_price` ;
- `created_at`.

La relation est :

`users.id -> predictions.user_id`

J'ai mis `ON DELETE CASCADE`. Ca veut dire que si un utilisateur est supprime,
ses predictions sont aussi supprimees. C'est utile pour garder une base propre.

### Table `exact_address_history`

Cette table stocke les recherches d'adresses exactes.

Colonnes principales :

- `id` : cle primaire ;
- `user_id` : cle etrangere vers `users(id)` ;
- `address` ;
- `latitude` ;
- `longitude` ;
- `created_at`.

La relation est :

`users.id -> exact_address_history.user_id`

J'ai aussi mis `ON DELETE CASCADE` pour supprimer les adresses si le compte est
supprime.

### Table `source_data_scraping`

Cette table stocke les annonces brutes du scraping.

Je garde les colonnes en `TEXT` parce que les donnees viennent directement des
sites web et peuvent avoir des formats differents.

Exemples :

- `prix` peut contenir un symbole euro ;
- `surface` peut contenir `m2` ;
- `nb_pieces` peut venir sous forme de texte.

### Table `master_data_scraping`

Cette table stocke les annonces apres un premier nettoyage.

Elle garde presque les memes colonnes que `source_data_scraping`, mais avec des
donnees deja plus propres.

Je l'utilise comme etape de controle avant d'aller vers la table finale.

### Table `golden_data_scraping`

Cette table est la table finale pour les annonces scraping.

Elle utilise des types plus stricts :

- `prix` en `NUMERIC` ;
- `surface` en `NUMERIC` ;
- `nb_pieces` en `INTEGER` ;
- `prix_m2` en `NUMERIC`.

C'est plus propre pour faire des calculs SQL, des statistiques et des endpoints
API.

### Table `dvf_paris_appartements`

Cette table stocke les ventes reelles DVF nettoyees.

Elle contient surtout :

- la date de vente ;
- la valeur fonciere ;
- le prix au m2 ;
- la surface ;
- le nombre de pieces ;
- l'arrondissement ;
- l'adresse ;
- la latitude et la longitude.

Cette table sert de base solide pour analyser le marche et entrainer le modele
de prediction.

## 5. Pourquoi il n'y a pas de cle etrangere partout

Dans mon projet, toutes les tables ne sont pas reliees avec des cles
etrangeres.

Les vraies cles etrangeres sont surtout :

- `predictions.user_id` vers `users.id` ;
- `exact_address_history.user_id` vers `users.id`.

Pour les tables scraping et DVF, je n'ai pas mis de cle etrangere parce que :

- les annonces scraping ne viennent pas de la meme source que DVF ;
- une annonce immobiliere n'est pas forcement egale a une vente DVF ;
- il peut y avoir des differences d'adresse, de date, de prix ou de surface ;
- le lien entre scraping et DVF sert surtout pour comparer et analyser, pas pour
  imposer une contrainte SQL.

Donc dans le schema, les liens entre `source`, `master`, `golden` et `DVF`
representent le pipeline et l'analyse, pas des relations SQL obligatoires.

## 6. Pourquoi source, master et golden

J'ai separe mes donnees scraping en trois niveaux.

### Source

La couche source garde les donnees comme elles arrivent au depart.

C'est important parce que si un nettoyage se passe mal, je peux revenir aux
donnees d'origine.

### Master

La couche master est une zone intermediaire.

Elle permet de corriger les formats, commencer a retirer les problemes et garder
une version plus stable.

### Golden

La couche golden est la version finale.

Elle est faite pour etre utilisee dans :

- les analyses SQL ;
- l'API ;
- les comparaisons avec DVF ;
- les futurs traitements IA.

Cette organisation me permet de ne pas melanger les donnees brutes et les
donnees finales.

## 7. Comment ouvrir le schema draw.io

Pour ouvrir le schema :

1. Aller sur draw.io ou diagrams.net.
2. Choisir ouvrir un fichier depuis l'ordinateur.
3. Selectionner le fichier `docs/schema_mcd_mld.drawio`.
4. Regarder les deux pages en bas :
   - `MCD`
   - `MLD`

Ensuite je peux exporter le schema en PNG ou PDF pour le mettre dans le dossier
final.

## 8. Verification avec DBeaver

Pour verifier que le MLD correspond bien a la base, j'ouvre DBeaver puis je vais
dans :

`Connexion PostgreSQL -> Databases -> <nom_base> -> Schemas -> public -> Tables`

Je dois retrouver les tables :

- `users`
- `predictions`
- `exact_address_history`
- `source_data_scraping`
- `master_data_scraping`
- `golden_data_scraping`
- `dvf_paris_appartements`

Si ces tables existent dans DBeaver, ca confirme que le MLD correspond bien a ma
base PostgreSQL.

## 9. Preuve Git

Le fichier draw.io est stocke dans le dossier `docs`, donc il peut etre suivi par
Git comme les autres documents du projet.

Pour verifier :

```bash
git status
```

Je dois voir :

```text
docs/schema_mcd_mld.drawio
docs/Rapport competence C4 - MCD MLD.md
```

Comme ca, le correcteur peut voir que le schema fait partie du projet et qu'il
n'est pas juste une image separee.

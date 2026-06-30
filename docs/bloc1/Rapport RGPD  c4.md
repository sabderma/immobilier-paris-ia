# Rapport RGPD - Bloc 1

## 1. Objectif du document

Ce document regroupe la partie RGPD du bloc 1.

Je l'ai mis a part pour ne pas melanger avec le rapport C4. Le rapport C4 parle
de la creation de la base, des tables, des imports et du stockage. Ici, je parle
uniquement des donnees personnelles, des regles de conservation et de la purge.

## 2. Donnees personnelles possibles dans le projet

Dans le projet, les donnees immobilieres comme DVF ou les annonces ne sont pas
les plus sensibles, car elles servent surtout aux statistiques.

Les donnees plus sensibles sont plutot les donnees liees aux utilisateurs :

- email de connexion ;
- prenom et nom si l'utilisateur les renseigne ;
- mot de passe hache ;
- historique des predictions ;
- adresse exacte recherchee ;
- latitude et longitude d'une adresse exacte.

Ces donnees sont stockees dans PostgreSQL, pas dans DBeaver. DBeaver sert juste
a visualiser la base.

## 3. Fichiers concernes

| Fichier | Role RGPD |
| --- | --- |
| `sql/creation_tables_utilisateurs.sql` | Cree les tables utilisateurs et historiques. |
| `scripts/purge_donnees_rgpd.py` | Simule ou execute la suppression des historiques trop anciens. |
| `api/services/auth.py` | Gere les comptes, les roles et les mots de passe haches. |
| `api/services/prediction_history.py` | Gere l'historique des predictions utilisateur. |
| `api/services/address_history.py` | Gere l'historique des adresses exactes. |

## 4. Tables concernees

### Table `users`

Cette table stocke les comptes utilisateurs.

Colonnes importantes :

- `id`
- `email`
- `password_hash`
- `first_name`
- `last_name`
- `role`
- `is_active`
- `created_at`
- `updated_at`

Le point important est que le mot de passe n'est pas stocke en clair. La colonne
s'appelle `password_hash`, donc elle doit contenir une version hachee du mot de
passe.

Il y a aussi un index unique sur l'email pour eviter deux comptes avec le meme
email.

### Table `predictions`

Cette table garde l'historique des predictions faites par l'utilisateur.

Elle contient :

- la surface ;
- le nombre de pieces ;
- l'arrondissement ;
- le prix predit ;
- la date de creation ;
- le lien vers l'utilisateur avec `user_id`.

Cette table est liee a `users(id)` avec `ON DELETE CASCADE`.

Ca veut dire que si un utilisateur est supprime, ses predictions peuvent etre
supprimees automatiquement aussi.

### Table `exact_address_history`

Cette table garde les adresses exactes recherchees par l'utilisateur.

Elle contient :

- l'adresse ;
- la latitude ;
- la longitude ;
- la date de creation ;
- le lien vers l'utilisateur avec `user_id`.

Une adresse exacte peut etre une donnee personnelle, parce qu'elle peut donner
une information precise sur une recherche faite par une personne.

Cette table est aussi liee a `users(id)` avec `ON DELETE CASCADE`.

## 5. Regles que j'applique

Mes regles simples dans le projet :

- ne pas stocker de mot de passe en clair ;
- stocker seulement `password_hash` ;
- ne pas mettre les mots de passe dans le code ;
- utiliser les variables d'environnement pour les secrets ;
- supprimer les historiques si le compte utilisateur est supprime ;
- prevoir une purge des historiques trop anciens ;
- eviter d'afficher une adresse complete dans les rapports de purge ;
- garder seulement les donnees utiles au fonctionnement de l'application.

## 6. Suppression en cascade

Dans `sql/creation_tables_utilisateurs.sql`, les tables `predictions` et
`exact_address_history` ont une cle etrangere vers `users`.

Exemple :

```sql
user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
```

Pourquoi c'est utile :

Si un compte utilisateur est supprime, les historiques lies a ce compte peuvent
etre supprimes automatiquement. Cela evite de garder des donnees utilisateur qui
ne sont plus rattachees a un compte.

## 7. Script de purge

Le script principal est :

`scripts/purge_donnees_rgpd.py`

Il travaille sur :

- `exact_address_history`
- `predictions`

Par defaut, il conserve les historiques pendant 365 jours.

Le script peut fonctionner en deux modes :

- simulation ;
- execution reelle.

## 8. Mode simulation

Commande :

```bash
python scripts/purge_donnees_rgpd.py
```

Ce mode ne supprime rien.

Il cree seulement un rapport pour montrer quelles lignes seraient concernees par
la purge.

C'est pratique parce que je peux verifier avant de supprimer pour de vrai.

## 9. Mode execution

Commande :

```bash
python scripts/purge_donnees_rgpd.py --execute
```

Ce mode supprime vraiment les lignes plus anciennes que la duree de conservation.

Le rapport produit est :

`data/raw/collecte/rapport_purge_rgpd.json`

## 10. Changer la duree de conservation

Je peux aussi changer la duree.

Exemple :

```bash
python scripts/purge_donnees_rgpd.py --jours-adresses 180 --jours-predictions 180
```

Ici, les adresses exactes et les predictions seraient conservees pendant 180
jours.

## 11. Pourquoi une simulation avant suppression

Je prefere avoir un mode simulation parce que la suppression de donnees est une
action importante.

Avec la simulation :

- je vois combien de lignes sont concernees ;
- je peux verifier les tables ;
- je peux eviter une suppression par erreur ;
- je garde une preuve avec un rapport JSON.

## 12. Ce que je ne stocke pas

Je ne stocke pas :

- le mot de passe en clair ;
- des documents d'identite ;
- des coordonnees bancaires ;
- des donnees personnelles qui ne servent pas au projet.

L'objectif est de garder seulement ce qui est utile.

## 13. Frequence conseillee

Pour mon projet, une purge peut etre lancee regulierement.

Par exemple :

- une fois par mois ;
- ou avant une livraison importante ;
- ou quand je veux nettoyer les historiques anciens.

## 14. Preuve Git

Les fichiers a suivre dans Git sont :

```bash
git ls-files scripts/purge_donnees_rgpd.py sql/creation_tables_utilisateurs.sql api/services/auth.py api/services/prediction_history.py api/services/address_history.py "docs/bloc1/Rapport RGPD - Bloc 1.md"
```

Ce document doit aussi etre ajoute au depot :

```bash
git add "docs/bloc1/Rapport RGPD - Bloc 1.md"
```

## 15. Conclusion personnelle

Pour le RGPD, j'ai separe le sujet dans un document a part.

Dans mon projet, les points principaux sont le mot de passe hache, les donnees
utilisateur limitees, la suppression en cascade et le script de purge des
historiques trop anciens.

Comme ca, le rapport C4 reste centre sur la base de donnees, et ce document
explique seulement la partie protection et conservation des donnees.

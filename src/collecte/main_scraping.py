"""Point d'entree court pour lancer le pipeline de collecte.

Le vrai travail est dans `pipeline_collecte.py`. Ce fichier permet juste de
lancer la collecte avec une commande simple depuis le dossier `src/collecte`.
"""

from pipeline_collecte import main


if __name__ == "__main__":
    raise SystemExit(main())

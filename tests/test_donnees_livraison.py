"""Tests C12 sur les donnees utilisees pour entrainer le modele IA.

Le but est de bloquer l'entrainement si le fichier DVF est absent ou si les
colonnes importantes ne sont pas propres.

En C13, GitHub Actions lance ces tests avant d'entrainer un nouveau modele.
En C19, ces memes tests passent avant la construction et la mise en ligne.
"""

from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DONNEES_ENTRAINEMENT = ROOT_DIR / "data/final/dvf_paris_clean_2021_2025.csv"
# C12 : ces colonnes sont obligatoires car le modele apprend avec elles.
COLONNES_OBLIGATOIRES = {
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "arrondissement",
    "valeur_fonciere",
}


class TestDonneesLivraisonModele(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Le CSV est charge une seule fois pour eviter de le relire a chaque test.
        cls.donnees = pd.read_csv(DONNEES_ENTRAINEMENT)

    def test_fichier_existe_et_contient_assez_de_ventes(self):
        # C12 : un modele IA doit avoir assez de donnees pour etre teste serieusement.
        self.assertTrue(DONNEES_ENTRAINEMENT.exists())
        self.assertGreaterEqual(len(self.donnees), 100000)

    def test_colonnes_obligatoires_sont_presentes(self):
        # Sans ces colonnes, l'entrainement XGBoost ne peut pas fonctionner.
        self.assertTrue(COLONNES_OBLIGATOIRES.issubset(self.donnees.columns))

    def test_donnees_obligatoires_ne_sont_pas_manquantes(self):
        # Les champs vides sont refuses avant d'arriver dans le modele.
        self.assertFalse(
            self.donnees[list(COLONNES_OBLIGATOIRES)].isna().any().any()
        )

    def test_valeurs_utilisees_par_le_modele_sont_valides(self):
        # C12 : on evite d'apprendre sur des surfaces, pieces ou prix impossibles.
        self.assertTrue((self.donnees["surface_reelle_bati"] > 0).all())
        self.assertTrue((self.donnees["nombre_pieces_principales"] > 0).all())
        self.assertTrue(self.donnees["arrondissement"].between(1, 20).all())
        self.assertTrue((self.donnees["valeur_fonciere"] > 0).all())

    def test_les_20_arrondissements_sont_representes(self):
        # Le projet concerne Paris, donc les 20 arrondissements doivent exister.
        arrondissements = set(self.donnees["arrondissement"].astype(int))
        self.assertEqual(arrondissements, set(range(1, 21)))


if __name__ == "__main__":
    unittest.main()

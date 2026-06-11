from __future__ import annotations

from pathlib import Path
import unittest

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DONNEES_ENTRAINEMENT = ROOT_DIR / "data/final/dvf_paris_clean_2021_2025.csv"
COLONNES_OBLIGATOIRES = {
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "arrondissement",
    "valeur_fonciere",
}


class TestDonneesLivraisonModele(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.donnees = pd.read_csv(DONNEES_ENTRAINEMENT)

    def test_fichier_existe_et_contient_assez_de_ventes(self):
        self.assertTrue(DONNEES_ENTRAINEMENT.exists())
        self.assertGreaterEqual(len(self.donnees), 100000)

    def test_colonnes_obligatoires_sont_presentes(self):
        self.assertTrue(COLONNES_OBLIGATOIRES.issubset(self.donnees.columns))

    def test_donnees_obligatoires_ne_sont_pas_manquantes(self):
        self.assertFalse(
            self.donnees[list(COLONNES_OBLIGATOIRES)].isna().any().any()
        )

    def test_valeurs_utilisees_par_le_modele_sont_valides(self):
        self.assertTrue((self.donnees["surface_reelle_bati"] > 0).all())
        self.assertTrue((self.donnees["nombre_pieces_principales"] > 0).all())
        self.assertTrue(self.donnees["arrondissement"].between(1, 20).all())
        self.assertTrue((self.donnees["valeur_fonciere"] > 0).all())

    def test_les_20_arrondissements_sont_representes(self):
        arrondissements = set(self.donnees["arrondissement"].astype(int))
        self.assertEqual(arrondissements, set(range(1, 21)))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import joblib
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.prediction import entrainement_xgboost_prix as entrainement  # noqa: E402
from src.prediction import prediction  # noqa: E402


class TestDonneesModele(unittest.TestCase):
    def test_charger_donnees_supprime_les_lignes_invalides(self):
        donnees = pd.DataFrame(
            [
                [50, 2, 11, 500000],
                [35, 1, 5, 350000],
                [0, 2, 11, 500000],
                [50, 0, 11, 500000],
                [50, 2, 21, 500000],
                [50, 2, 11, -1],
                [None, 2, 11, 500000],
            ],
            columns=entrainement.FEATURES + [entrainement.TARGET],
        )

        with tempfile.TemporaryDirectory() as dossier_temporaire:
            chemin_csv = Path(dossier_temporaire) / "donnees_test.csv"
            donnees.to_csv(chemin_csv, index=False)

            x, y = entrainement.charger_donnees(chemin_csv)

        self.assertEqual(list(x.columns), entrainement.FEATURES)
        self.assertEqual(len(x), 2)
        self.assertEqual(len(y), 2)
        self.assertFalse(x.isna().any().any())
        self.assertFalse(y.isna().any())
        self.assertTrue((x["surface_reelle_bati"] > 0).all())
        self.assertTrue((x["nombre_pieces_principales"] > 0).all())
        self.assertTrue(x["arrondissement"].astype(int).between(1, 20).all())
        self.assertTrue((y > 0).all())


class TestPreparationPrediction(unittest.TestCase):
    def test_preparer_donnees_prediction_cree_le_format_attendu(self):
        donnees = prediction.preparer_donnees_prediction(
            surface=50,
            nombre_pieces=2,
            arrondissement=11,
        )

        self.assertEqual(list(donnees.columns), entrainement.FEATURES)
        self.assertEqual(len(donnees), 1)
        self.assertEqual(donnees.iloc[0]["surface_reelle_bati"], 50)
        self.assertEqual(donnees.iloc[0]["nombre_pieces_principales"], 2)
        self.assertEqual(donnees.iloc[0]["arrondissement"], "11")


class TestEntrainementModele(unittest.TestCase):
    def test_entrainement_cree_un_modele_et_des_metriques(self):
        donnees = pd.DataFrame(
            [
                [20, 1, 1, 220000],
                [30, 1, 2, 310000],
                [40, 2, 3, 420000],
                [50, 2, 4, 510000],
                [60, 3, 5, 630000],
                [70, 3, 6, 720000],
                [80, 4, 7, 840000],
                [90, 4, 8, 930000],
            ],
            columns=entrainement.FEATURES + [entrainement.TARGET],
        )

        modele_rapide = entrainement.construire_modele()
        modele_rapide.set_params(
            modele__n_estimators=2,
            modele__max_depth=2,
            modele__n_jobs=1,
        )

        with tempfile.TemporaryDirectory() as dossier_temporaire:
            dossier = Path(dossier_temporaire)
            chemin_csv = dossier / "donnees_entrainement.csv"
            chemin_modele = dossier / "modele.joblib"
            chemin_metriques = dossier / "metriques.json"
            donnees.to_csv(chemin_csv, index=False)

            with patch.object(
                entrainement,
                "construire_modele",
                return_value=modele_rapide,
            ):
                modele, metriques = entrainement.entrainer_xgboost(
                    input_csv=chemin_csv,
                    output_model=chemin_modele,
                    output_metrics=chemin_metriques,
                    test_size=0.25,
                    random_state=42,
                )

            self.assertTrue(chemin_modele.exists())
            self.assertTrue(chemin_metriques.exists())
            self.assertEqual(metriques["lignes_total"], 8)
            self.assertEqual(metriques["lignes_train"], 6)
            self.assertEqual(metriques["lignes_test"], 2)
            self.assertIn("r2_score", metriques)
            self.assertIn("mae_euros", metriques)
            self.assertIn("rmse_euros", metriques)

            modele_recharge = joblib.load(chemin_modele)
            prix = entrainement.predire_prix(modele_recharge, 50, 2, 4)

        self.assertIs(modele, modele_rapide)
        self.assertTrue(math.isfinite(prix))
        self.assertGreater(prix, 0)


class TestModeleEnregistre(unittest.TestCase):
    def test_modele_enregistre_retourne_un_prix_positif(self):
        chemin_modele = ROOT_DIR / "models/xgboost_prix_dvf.joblib"

        prix = prediction.predire_prix(
            surface=50,
            nombre_pieces=2,
            arrondissement=11,
            model_path=chemin_modele,
        )

        self.assertIsInstance(prix, float)
        self.assertTrue(math.isfinite(prix))
        self.assertGreater(prix, 0)

    def test_qualite_enregistree_respecte_le_seuil_r2(self):
        chemin_metriques = ROOT_DIR / "models/xgboost_prix_dvf_metrics.json"
        metriques = json.loads(chemin_metriques.read_text(encoding="utf-8"))

        self.assertGreaterEqual(metriques["r2_score"], 0.80)
        self.assertGreater(metriques["mae_euros"], 0)
        self.assertGreater(metriques["rmse_euros"], 0)


if __name__ == "__main__":
    unittest.main()

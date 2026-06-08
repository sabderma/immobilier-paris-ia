from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

os.environ["API_KEY"] = "test-api-key"

from api import main  # noqa: E402
from api.routers import dvf as dvf_router  # noqa: E402
from api.routers import location as location_router  # noqa: E402
from api.routers import prediction as prediction_router  # noqa: E402
from api.routers import stats as stats_router  # noqa: E402
from api.services import commerces as commerces_service  # noqa: E402


client = TestClient(main.app)
AUTH_HEADERS = {"X-API-Key": os.environ["API_KEY"]}


def fake_lire_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    if "FROM dvf_paris_appartements" in query:
        return pd.DataFrame(
            [
                {
                    "id": 1,
                    "id_mutation": "2024-1",
                    "date_mutation": "2024-01-15",
                    "annee_vente": 2024,
                    "mois_vente": 1,
                    "valeur_fonciere": 450000.0,
                    "prix_m2": 10000.0,
                    "surface_reelle_bati": 45.0,
                    "nombre_pieces_principales": 2,
                    "type_local": "Appartement",
                    "code_postal": "75011",
                    "arrondissement": 11,
                    "nom_commune": "Paris",
                    "adresse_nom_voie": "Rue de test",
                    "longitude": 2.38,
                    "latitude": 48.85,
                }
            ]
        )

    return pd.DataFrame()


class TestApiSecurity(unittest.TestCase):
    def test_accueil_est_public(self):
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "API Immobilier Paris fonctionne",
        )

    def test_points_dvf_refuse_une_requete_sans_cle_api(self):
        response = client.get("/dvf/points")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Clé API manquante")

    def test_points_dvf_refuse_une_mauvaise_cle_api(self):
        response = client.get("/dvf/points", headers={"X-API-Key": "mauvaise-cle"})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Clé API invalide")

    def test_points_dvf_accepte_une_bonne_cle_api(self):
        with patch.object(dvf_router, "lire_sql", side_effect=fake_lire_sql):
            response = client.get("/dvf/points?limit=1", headers=AUTH_HEADERS)

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["nombre_resultats"], 1)
        self.assertEqual(payload["limite"], 1)
        self.assertEqual(payload["data"][0]["arrondissement"], 11)

    def test_routes_non_utilisees_ne_sont_plus_exposees(self):
        for path in ["/annonces", "/dvf", "/stats/dvf/evolution-annuelle"]:
            with self.subTest(path=path):
                response = client.get(path, headers=AUTH_HEADERS)

                self.assertEqual(response.status_code, 404)

    def test_resume_dvf_retourne_les_indicateurs_attendus(self):
        def fake_resume_sql(query: str, params: dict | None = None) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {
                        "nombre_ventes": 10,
                        "prix_m2_median": 10500.0,
                        "prix_moyen_vente": 520000.0,
                        "surface_moyenne": 48.5,
                    }
                ]
            )

        with patch.object(stats_router, "lire_sql", side_effect=fake_resume_sql):
            response = client.get("/stats/dvf/resume", headers=AUTH_HEADERS)

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(payload),
            {
                "nombre_ventes",
                "prix_m2_median",
                "prix_moyen_vente",
                "surface_moyenne",
            },
        )

    def test_export_csv_demande_une_cle_api(self):
        response = client.get("/dvf/export.csv")

        self.assertEqual(response.status_code, 401)

    def test_prediction_prix_retourne_un_prix_estime(self):
        payload = {
            "surface": 45,
            "nombre_pieces": 2,
            "arrondissement": 11,
        }

        with (
            patch.object(
                prediction_router,
                "predire_prix_xgboost",
                return_value=465328.0,
            ),
            patch.object(
                prediction_router,
                "charger_mae_prediction",
                return_value=111078.36,
            ),
        ):
            response = client.post(
                "/prediction/prix",
                json=payload,
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prix_estime"], 465328.0)
        self.assertEqual(response.json()["mae_euros"], 111078.36)
        self.assertEqual(response.json()["prix_min_indicatif"], 354249.64)
        self.assertEqual(response.json()["prix_max_indicatif"], 576406.36)
        self.assertEqual(response.json()["modele"], "XGBRegressor")

    def test_metrics_expose_erreur_moyenne_modele(self):
        response = client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'model_evaluation_mae_euros{model="XGBRegressor"}',
            response.text,
        )
        self.assertIn(
            'model_evaluation_test_samples{model="XGBRegressor"}',
            response.text,
        )

    def test_noter_adresse_refuse_une_adresse_hors_paris(self):
        response = client.post(
            "/ia/noter-adresse",
            json={"adresse": "10 rue Victor Hugo, 69002 Lyon", "arrondissement": 11},
            headers=AUTH_HEADERS,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["erreur"], "Adresse non valide")
        self.assertEqual(
            response.json()["message"],
            "Il faut saisir une adresse située à Paris.",
        )

    def test_noter_adresse_refuse_un_arrondissement_incoherent(self):
        response = client.post(
            "/ia/noter-adresse",
            json={"adresse": "71 rue de Passy, Paris 16e", "arrondissement": 2},
            headers=AUTH_HEADERS,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["erreur"], "Arrondissement incohérent")
        self.assertIn("Paris 16", response.json()["message"])
        self.assertIn("Paris 2", response.json()["message"])

    def test_noter_adresse_demande_une_adresse_complete(self):
        response = client.post(
            "/ia/noter-adresse",
            json={"adresse": "71 rue de Passy"},
            headers=AUTH_HEADERS,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["erreur"], "Adresse incomplète")

    def test_noter_adresse_appelle_gemini_pour_une_adresse_parisienne(self):
        resultat_gemini = {
            "adresse_analysee": "71 rue de Passy, Paris 16",
            "score_global": 92,
            "niveau": "excellent",
            "resume": "Adresse très bien située.",
            "details": {},
            "points_forts": ["Transports proches"],
            "points_faibles": ["Rue commerçante"],
            "conclusion_acheteur": "Très bon emplacement.",
        }

        with patch.object(
            location_router,
            "generer_score_adresse_gemini",
            return_value=resultat_gemini,
        ) as gemini:
            response = client.post(
                "/ia/noter-adresse",
                json={"adresse": "71 rue de Passy, Paris 16e"},
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["score_global"], 92)
        gemini.assert_called_once_with("71 rue de Passy, Paris 16e", 16)

    def test_commerces_paris_retourne_un_arrondissement_normalise(self):
        reponse_api = Mock()
        reponse_api.raise_for_status.return_value = None
        reponse_api.json.return_value = {
            "results": [
                {
                    "departement_commune": 75111,
                    "libelle_de_commune": ["Paris 11e Arrondissement"],
                    "population_2010": 153202,
                    "supermarche": 28,
                    "superette": 29,
                    "epicerie": 154,
                    "boulangerie": 128,
                    "boucherie_charcuterie": 68,
                    "poissonnerie": 7,
                    "fleuriste": 54,
                    "geo_point_2d": {"lat": 48.8594, "lon": 2.3787},
                }
            ]
        }

        location_router.charger_commerces_paris.cache_clear()
        with patch.object(commerces_service.requests, "get", return_value=reponse_api):
            response = client.get(
                "/commerces/paris?arrondissement=11",
                headers=AUTH_HEADERS,
            )
        location_router.charger_commerces_paris.cache_clear()

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["nombre_resultats"], 1)
        self.assertEqual(payload["data"][0]["arrondissement"], 11)
        self.assertEqual(payload["data"][0]["nom_arrondissement"], "Paris 11e Arrondissement")
        self.assertEqual(payload["data"][0]["commerces_alimentaires"], 386)
        self.assertEqual(payload["data"][0]["note_commerces_sur_10"], 10.0)


if __name__ == "__main__":
    unittest.main()

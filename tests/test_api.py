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
from api.routers import scraping as scraping_router  # noqa: E402
from api.routers import stats as stats_router  # noqa: E402
from api.services import address as address_service  # noqa: E402
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

    def test_annonces_scraping_utilisent_la_table_golden_et_les_filtres(self):
        annonces = pd.DataFrame(
            [
                {
                    "id": 1,
                    "source": "orpi",
                    "type": "Appartement",
                    "prix": 550000.0,
                    "surface": 50.0,
                    "nb_pieces": 2,
                    "localisation": "75011",
                    "arrondissement": 11,
                    "prix_m2": 11000.0,
                    "date_scraping": "2025-05-15",
                }
            ]
        )

        total = pd.DataFrame([{"nombre_total": 42}])
        with patch.object(
            scraping_router,
            "lire_sql",
            side_effect=[total, annonces],
        ) as lire_sql:
            response = client.get(
                "/scraping/annonces?arrondissement=11&source=orpi&limit=10&offset=20",
                headers=AUTH_HEADERS,
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["nombre_resultats"], 1)
        self.assertEqual(payload["nombre_total"], 42)
        self.assertEqual(payload["offset"], 20)
        self.assertEqual(payload["data"][0]["source"], "orpi")
        query, params = lire_sql.call_args_list[1].args
        self.assertIn("FROM golden_data_scraping", query)
        self.assertIn("OFFSET :offset", query)
        self.assertEqual(params["localisation"], "75011")
        self.assertEqual(params["source"], "orpi")
        self.assertEqual(params["limit"], 10)
        self.assertEqual(params["offset"], 20)

    def test_annonces_scraping_demandent_une_cle_api(self):
        response = client.get("/scraping/annonces")

        self.assertEqual(response.status_code, 401)

    def test_resume_scraping_retourne_les_indicateurs_attendus(self):
        resume = pd.DataFrame(
            [
                {
                    "nombre_annonces": 4375,
                    "prix_median": 624000.0,
                    "prix_m2_median": 10993.0,
                    "date_mise_a_jour": "2025-05-15",
                }
            ]
        )

        with patch.object(scraping_router, "lire_sql", return_value=resume):
            response = client.get("/stats/scraping/resume", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nombre_annonces"], 4375)
        self.assertEqual(response.json()["prix_m2_median"], 10993.0)

    def test_comparaison_scraping_dvf_limite_dvf_a_2025(self):
        scraping = pd.DataFrame(
            [{"arrondissement": 11, "prix_m2_scraping": 11500.0}]
        )
        dvf = pd.DataFrame([{"arrondissement": 11, "prix_m2_dvf": 10200.0}])

        with patch.object(
            scraping_router,
            "lire_sql",
            side_effect=[scraping, dvf],
        ) as lire_sql:
            response = client.get(
                "/stats/scraping/comparaison-dvf-2025",
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["prix_m2_scraping"], 11500.0)
        self.assertEqual(response.json()[0]["prix_m2_dvf"], 10200.0)
        requete_dvf, params_dvf = lire_sql.call_args_list[1].args
        self.assertIn("FROM dvf_paris_appartements", requete_dvf)
        self.assertEqual(params_dvf["annee_vente"], 2025)

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

    def test_appel_gemini_utilise_un_modele_de_secours(self):
        client_gemini = Mock()
        reponse_gemini = Mock()
        client_gemini.models.generate_content.side_effect = [
            RuntimeError("503 UNAVAILABLE: high demand"),
            reponse_gemini,
        ]

        with patch.object(address_service.time, "sleep") as sleep:
            resultat = address_service.appeler_gemini_avec_repli(
                client_gemini,
                ["gemini-principal", "gemini-secours"],
                "prompt",
            )

        self.assertIs(resultat, reponse_gemini)
        self.assertEqual(client_gemini.models.generate_content.call_count, 2)
        self.assertEqual(
            [
                appel.kwargs["model"]
                for appel in client_gemini.models.generate_content.call_args_list
            ],
            ["gemini-principal", "gemini-secours"],
        )
        sleep.assert_not_called()

    def test_appel_gemini_ne_change_pas_de_modele_apres_une_erreur_definitive(self):
        client_gemini = Mock()
        client_gemini.models.generate_content.side_effect = RuntimeError(
            "Requête invalide"
        )

        with (
            patch.object(address_service.time, "sleep") as sleep,
            self.assertRaisesRegex(RuntimeError, "Requête invalide"),
        ):
            address_service.appeler_gemini_avec_repli(
                client_gemini,
                ["gemini-principal", "gemini-secours"],
                "prompt",
            )

        self.assertEqual(client_gemini.models.generate_content.call_count, 1)
        sleep.assert_not_called()

    def test_modeles_gemini_configures_supprime_les_doublons(self):
        with patch.dict(
            os.environ,
            {
                "GEMINI_MODEL": "gemini-principal",
                "GEMINI_FALLBACK_MODELS": "gemini-secours, gemini-principal",
            },
        ):
            modeles = address_service.modeles_gemini_configures()

        self.assertEqual(modeles, ["gemini-principal", "gemini-secours"])

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

from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from fastapi import HTTPException
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
from api.routers import users as users_router  # noqa: E402
from api.services import auth as auth_service  # noqa: E402
from api.services import address as address_service  # noqa: E402
from api.services import commerces as commerces_service  # noqa: E402
from api.services import location_summary as location_summary_service  # noqa: E402
from api.services import proximity as proximity_service  # noqa: E402


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
    def tearDown(self):
        main.app.dependency_overrides.clear()

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
            patch.object(
                prediction_router,
                "enregistrer_prediction_utilisateur",
            ) as enregistrer_prediction,
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
        enregistrer_prediction.assert_not_called()

    def test_prediction_connectee_est_enregistree_dans_l_historique(self):
        payload = {
            "surface": 45,
            "nombre_pieces": 2,
            "arrondissement": 11,
        }
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_optionnel] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

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
            patch.object(
                prediction_router,
                "enregistrer_prediction_utilisateur",
            ) as enregistrer_prediction,
        ):
            response = client.post(
                "/prediction/prix",
                json=payload,
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        enregistrer_prediction.assert_called_once_with(
            user_id=7,
            surface=45.0,
            nombre_pieces=2,
            arrondissement=11,
            predicted_price=465328.0,
        )

    def test_historique_predictions_retourne_les_predictions_de_l_utilisateur(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )
        historique = [
            {
                "id": 3,
                "user_id": 7,
                "surface": 45.0,
                "nb_pieces": 2,
                "arrondissement": 11,
                "predicted_price": 465328.0,
                "created_at": "2026-06-16T19:00:00Z",
            }
        ]

        with patch.object(
            users_router,
            "lister_predictions_utilisateur",
            return_value=historique,
        ) as lister_predictions:
            response = client.get("/users/me/predictions")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["user_id"], 7)
        self.assertEqual(response.json()[0]["nb_pieces"], 2)
        self.assertEqual(response.json()[0]["predicted_price"], 465328.0)
        lister_predictions.assert_called_once_with(7)

    def test_suppression_prediction_supprime_uniquement_celle_de_l_utilisateur(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with patch.object(
            users_router,
            "supprimer_prediction_utilisateur",
            return_value=True,
        ) as supprimer_prediction:
            response = client.delete("/users/me/predictions/3")

        self.assertEqual(response.status_code, 204)
        supprimer_prediction.assert_called_once_with(user_id=7, prediction_id=3)

    def test_suppression_prediction_retourne_404_si_absente_ou_autre_utilisateur(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with patch.object(
            users_router,
            "supprimer_prediction_utilisateur",
            return_value=False,
        ):
            response = client.delete("/users/me/predictions/99")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Prédiction introuvable.")

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

    def test_route_geocodage_retourne_adresse_normalisee(self):
        resultat_ign = {
            "source": "Géoplateforme IGN - Base Adresse Nationale",
            "adresse_saisie": "71 rue de Passy, Paris 16e",
            "adresse_normalisee": "71 Rue de Passy 75016 Paris",
            "longitude": 2.277151,
            "latitude": 48.857919,
            "score_correspondance": 0.9793,
            "arrondissement": 16,
        }
        resultat_proximite = {
            "rayon_metres": 500,
            "distance": "à vol d'oiseau",
            "transports": [],
            "equipements": [],
            "erreurs": [],
            "totaux": {
                "transports": 0,
                "commerces": 0,
                "education": 0,
                "sante": 0,
            },
        }
        resultat_resume = {
            "texte": "Le secteur dispose de plusieurs services à proximité.",
            "modele": "gpt-5.4-mini",
            "source": "OpenAI",
        }

        with (
            patch.object(
                location_router,
                "geocoder_adresse_ign",
                return_value=resultat_ign,
            ) as geocoder,
            patch.object(
                location_router,
                "analyser_proximite",
                return_value=resultat_proximite,
            ) as analyser_proximite,
            patch.object(
                location_router,
                "generer_resume_lieu",
                return_value=resultat_resume,
            ) as generer_resume_lieu,
            patch.object(
                location_router,
                "enregistrer_adresse_utilisateur",
            ) as enregistrer_adresse,
        ):
            response = client.post(
                "/geocodage/adresse",
                json={"adresse": "71 rue de Passy, Paris 16e"},
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["adresse_normalisee"],
            "71 Rue de Passy 75016 Paris",
        )
        self.assertEqual(response.json()["proximite"], resultat_proximite)
        self.assertEqual(response.json()["resume_ia"], resultat_resume)
        geocoder.assert_called_once_with("71 rue de Passy, Paris 16e")
        analyser_proximite.assert_called_once_with(48.857919, 2.277151)
        generer_resume_lieu.assert_called_once_with(
            "71 Rue de Passy 75016 Paris",
            resultat_proximite,
        )
        enregistrer_adresse.assert_not_called()

    def test_geocodage_connecte_enregistre_l_adresse_validee(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_optionnel] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )
        resultat_ign = {
            "source": "Géoplateforme IGN - Base Adresse Nationale",
            "adresse_saisie": "71 rue de Passy, Paris 16e",
            "adresse_normalisee": "71 Rue de Passy 75016 Paris",
            "longitude": 2.277151,
            "latitude": 48.857919,
            "score_correspondance": 0.9793,
            "arrondissement": 16,
        }

        with (
            patch.object(
                location_router,
                "geocoder_adresse_ign",
                return_value=resultat_ign,
            ),
            patch.object(
                location_router,
                "analyser_proximite",
                return_value={"totaux": {}},
            ),
            patch.object(
                location_router,
                "generer_resume_lieu",
                return_value={"texte": "Résumé"},
            ),
            patch.object(
                location_router,
                "enregistrer_adresse_utilisateur",
            ) as enregistrer_adresse,
        ):
            response = client.post(
                "/geocodage/adresse",
                json={"adresse": "71 rue de Passy, Paris 16e"},
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        enregistrer_adresse.assert_called_once_with(
            user_id=7,
            address="71 Rue de Passy 75016 Paris",
            latitude=48.857919,
            longitude=2.277151,
        )

    def test_geocodage_connecte_n_enregistre_pas_une_adresse_invalide(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_optionnel] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with (
            patch.object(
                location_router,
                "geocoder_adresse_ign",
                return_value={
                    "erreur": "Adresse non valide",
                    "message": "Il faut saisir une adresse exacte située à Paris.",
                },
            ),
            patch.object(
                location_router,
                "enregistrer_adresse_utilisateur",
            ) as enregistrer_adresse,
        ):
            response = client.post(
                "/geocodage/adresse",
                json={"adresse": "10 rue Victor Hugo, Lyon"},
                headers=AUTH_HEADERS,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["erreur"], "Adresse non valide")
        enregistrer_adresse.assert_not_called()

    def test_historique_adresses_retourne_les_adresses_de_l_utilisateur(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )
        historique = [
            {
                "id": 4,
                "user_id": 7,
                "address": "71 Rue de Passy 75016 Paris",
                "latitude": 48.857919,
                "longitude": 2.277151,
                "created_at": "2026-06-16T19:00:00Z",
            }
        ]

        with patch.object(
            users_router,
            "lister_adresses_utilisateur",
            return_value=historique,
        ) as lister_adresses:
            response = client.get("/users/me/addresses")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["user_id"], 7)
        self.assertEqual(response.json()[0]["address"], "71 Rue de Passy 75016 Paris")
        lister_adresses.assert_called_once_with(7)

    def test_suppression_adresse_supprime_uniquement_celle_de_l_utilisateur(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with patch.object(
            users_router,
            "supprimer_adresse_utilisateur",
            return_value=True,
        ) as supprimer_adresse:
            response = client.delete("/users/me/addresses/4")

        self.assertEqual(response.status_code, 204)
        supprimer_adresse.assert_called_once_with(user_id=7, address_id=4)

    def test_suppression_adresse_retourne_404_si_absente_ou_autre_utilisateur(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with patch.object(
            users_router,
            "supprimer_adresse_utilisateur",
            return_value=False,
        ):
            response = client.delete("/users/me/addresses/99")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Adresse introuvable.")

    def test_modification_profil_met_a_jour_nom_et_prenom(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {
                "id": 7,
                "email": "test@example.com",
                "first_name": "Malek",
                "last_name": "Silarbi",
                "role": "user",
            }
        )
        utilisateur_modifie = {
            "id": 7,
            "email": "test@example.com",
            "first_name": "Nouveau",
            "last_name": "Nom",
            "role": "user",
            "created_at": "2026-06-16T19:00:00Z",
        }

        with patch.object(
            users_router,
            "mettre_a_jour_profil_utilisateur",
            return_value=utilisateur_modifie,
        ) as mettre_a_jour_profil:
            response = client.patch(
                "/users/me/profile",
                json={"first_name": " Nouveau ", "last_name": " Nom "},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], "Nouveau")
        self.assertEqual(response.json()["last_name"], "Nom")
        mettre_a_jour_profil.assert_called_once_with(
            user_id=7,
            first_name="Nouveau",
            last_name="Nom",
        )

    def test_modification_profil_refuse_un_payload_vide(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {
                "id": 7,
                "email": "test@example.com",
                "first_name": "Malek",
                "last_name": "Silarbi",
                "role": "user",
            }
        )

        response = client.patch("/users/me/profile", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Aucune information à modifier.")

    def test_modification_mot_de_passe_verifie_l_ancien_mot_de_passe(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with patch.object(
            users_router,
            "changer_mot_de_passe_utilisateur",
        ) as changer_mot_de_passe:
            response = client.patch(
                "/users/me/password",
                json={
                    "current_password": "ancien-mot-de-passe",
                    "new_password": "nouveau-mot-de-passe",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Mot de passe modifié avec succès.",
        )
        changer_mot_de_passe.assert_called_once_with(
            user_id=7,
            current_password="ancien-mot-de-passe",
            new_password="nouveau-mot-de-passe",
        )

    def test_modification_mot_de_passe_refuse_un_mot_de_passe_trop_court(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        response = client.patch(
            "/users/me/password",
            json={"current_password": "ancien", "new_password": "court"},
        )

        self.assertEqual(response.status_code, 422)

    def test_modification_mot_de_passe_refuse_un_ancien_mot_de_passe_incorrect(self):
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: {"id": 7, "email": "test@example.com", "role": "user"}
        )

        with patch.object(
            users_router,
            "changer_mot_de_passe_utilisateur",
            side_effect=HTTPException(
                status_code=401,
                detail="Mot de passe actuel incorrect.",
            ),
        ):
            response = client.patch(
                "/users/me/password",
                json={
                    "current_password": "mauvais",
                    "new_password": "nouveau-mot-de-passe",
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Mot de passe actuel incorrect.")

    def test_resume_openai_utilise_uniquement_les_donnees_de_proximite(self):
        proximite = {
            "rayon_metres": 500,
            "distance": "à vol d'oiseau",
            "totaux": {
                "transports": 2,
                "commerces": 8,
                "education": 1,
                "sante": 2,
            },
            "transports": [
                {
                    "nom": "Passy",
                    "modes": ["Métro"],
                    "lignes": ["6"],
                    "distance_metres": 180,
                    "latitude": 48.0,
                    "longitude": 2.0,
                }
            ],
            "equipements": [
                {
                    "nom": "Boulangerie Test",
                    "categorie": "commerce",
                    "sous_categorie": "bakery",
                    "distance_metres": 70,
                    "latitude": 48.0,
                    "longitude": 2.0,
                }
            ],
        }
        reponse_openai = Mock(
            output_text="Le métro Passy et des commerces sont proches."
        )
        client_openai = Mock()
        client_openai.responses.create.return_value = reponse_openai

        with (
            patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-openai-key",
                    "OPENAI_MODEL": "gpt-5.4-mini",
                },
            ),
            patch.object(location_summary_service, "charger_env"),
            patch.object(
                location_summary_service,
                "OpenAI",
                return_value=client_openai,
            ) as openai,
        ):
            resultat = location_summary_service.generer_resume_lieu(
                "71 Rue de Passy 75016 Paris",
                proximite,
            )

        self.assertEqual(
            resultat["texte"],
            "Le métro Passy et des commerces sont proches.",
        )
        self.assertEqual(resultat["modele"], "gpt-5.4-mini")
        openai.assert_called_once_with(
            api_key="test-openai-key",
            timeout=location_summary_service.TIMEOUT_OPENAI_SECONDES,
            max_retries=1,
        )
        appel = client_openai.responses.create.call_args.kwargs
        self.assertEqual(appel["model"], "gpt-5.4-mini")
        self.assertFalse(appel["store"])
        self.assertNotIn("latitude", appel["input"])
        self.assertNotIn("longitude", appel["input"])
        self.assertIn("Passy", appel["input"])

    def test_resume_openai_reste_optionnel_sans_cle(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(location_summary_service, "charger_env"),
        ):
            resultat = location_summary_service.generer_resume_lieu(
                "71 Rue de Passy 75016 Paris",
                {"totaux": {}},
            )

        self.assertEqual(
            resultat,
            {"erreur": "Le résumé OpenAI n'est pas configuré."},
        )

    def test_geocodage_ign_normalise_une_adresse_parisienne_exacte(self):
        reponse_ign = Mock()
        reponse_ign.raise_for_status.return_value = None
        reponse_ign.json.return_value = {
            "features": [
                {
                    "geometry": {
                        "type": "Point",
                        "coordinates": [2.277151, 48.857919],
                    },
                    "properties": {
                        "label": "71 Rue de Passy 75016 Paris",
                        "score": 0.979341818181818,
                        "housenumber": "71",
                        "id": "75116_7087_00071",
                        "postcode": "75016",
                        "city": "Paris",
                        "type": "housenumber",
                        "street": "Rue de Passy",
                    },
                }
            ]
        }

        with patch.object(address_service.requests, "get", return_value=reponse_ign) as get:
            resultat = address_service.geocoder_adresse_ign(
                "  71   rue de Passy, Paris 16e "
            )

        self.assertEqual(resultat["adresse_saisie"], "71 rue de Passy, Paris 16e")
        self.assertEqual(resultat["adresse_normalisee"], "71 Rue de Passy 75016 Paris")
        self.assertEqual(resultat["arrondissement"], 16)
        self.assertEqual(resultat["longitude"], 2.277151)
        self.assertEqual(resultat["latitude"], 48.857919)
        self.assertEqual(resultat["score_correspondance"], 0.9793)
        get.assert_called_once_with(
            address_service.GEOCODAGE_IGN_API_URL,
            params={
                "q": "71 rue de Passy, Paris 16e",
                "limit": 5,
                "index": "address",
            },
            timeout=address_service.TIMEOUT_GEOCODAGE_SECONDES,
        )

    def test_geocodage_ign_refuse_une_adresse_hors_paris(self):
        reponse_ign = Mock()
        reponse_ign.raise_for_status.return_value = None
        reponse_ign.json.return_value = {
            "features": [
                {
                    "properties": {
                        "label": "10 Rue Victor Hugo 69002 Lyon",
                        "postcode": "69002",
                        "city": "Lyon",
                        "type": "housenumber",
                    }
                }
            ]
        }

        with patch.object(address_service.requests, "get", return_value=reponse_ign):
            resultat = address_service.geocoder_adresse_ign(
                "10 rue Victor Hugo, 69002 Lyon"
            )

        self.assertEqual(resultat["erreur"], "Adresse non valide")

    def test_geocodage_ign_demande_un_numero_de_voie(self):
        reponse_ign = Mock()
        reponse_ign.raise_for_status.return_value = None
        reponse_ign.json.return_value = {
            "features": [
                {
                    "properties": {
                        "label": "Rue de Passy 75016 Paris",
                        "postcode": "75016",
                        "city": "Paris",
                        "type": "street",
                    }
                }
            ]
        }

        with patch.object(address_service.requests, "get", return_value=reponse_ign):
            resultat = address_service.geocoder_adresse_ign("rue de Passy, Paris")

        self.assertEqual(resultat["erreur"], "Adresse exacte introuvable")

    def test_geocodage_ign_signale_une_indisponibilite(self):
        with patch.object(
            address_service.requests,
            "get",
            side_effect=address_service.requests.ConnectionError("indisponible"),
        ):
            with self.assertRaises(HTTPException) as contexte:
                address_service.geocoder_adresse_ign("71 rue de Passy, Paris")

        self.assertEqual(contexte.exception.status_code, 503)
        self.assertEqual(
            contexte.exception.detail,
            "Le service de géocodage IGN est temporairement indisponible.",
        )

    def test_transports_idfm_retourne_arrets_modes_et_lignes(self):
        reponse_idfm = Mock()
        reponse_idfm.raise_for_status.return_value = None
        reponse_idfm.json.return_value = {
            "places_nearby": [
                {
                    "id": "stop_area:test",
                    "name": "Passy",
                    "distance": 212,
                    "stop_area": {
                        "id": "stop_area:test",
                        "name": "Passy",
                        "coord": {"lat": "48.8581", "lon": "2.2852"},
                        "commercial_modes": [{"name": "Métro"}],
                        "lines": [{"code": "6"}, {"code": "6"}],
                    },
                }
            ]
        }

        with (
            patch.dict(os.environ, {"IDFM_API_KEY": "test-idfm-key"}),
            patch.object(proximity_service, "charger_env"),
            patch.object(
                proximity_service.requests,
                "get",
                return_value=reponse_idfm,
            ) as get,
        ):
            resultat = proximity_service.chercher_transports_idfm(
                48.857919,
                2.277151,
            )

        self.assertEqual(resultat[0]["nom"], "Passy")
        self.assertEqual(resultat[0]["modes"], ["Métro"])
        self.assertEqual(resultat[0]["lignes"], ["6"])
        self.assertEqual(resultat[0]["distance_metres"], 212)
        self.assertEqual(get.call_args.kwargs["headers"], {"apikey": "test-idfm-key"})
        self.assertEqual(get.call_args.kwargs["params"]["distance"], 500)

    def test_transports_idfm_utilise_open_data_si_prim_est_indisponible(self):
        reponse_open_data = Mock()
        reponse_open_data.raise_for_status.return_value = None
        reponse_open_data.json.return_value = {
            "results": [
                {
                    "stop_id": "IDFM:463203",
                    "stop_name": "La Muette",
                    "mode": "Metro",
                    "shortname": "9",
                    "pointgeo": {"lat": 48.858092, "lon": 2.274096},
                },
                {
                    "stop_id": "IDFM:463203",
                    "stop_name": "La Muette",
                    "mode": "Metro",
                    "shortname": "9",
                    "pointgeo": {"lat": 48.858092, "lon": 2.274096},
                },
            ]
        }

        with (
            patch.dict(os.environ, {"IDFM_API_KEY": "test-idfm-key"}),
            patch.object(proximity_service, "charger_env"),
            patch.object(
                proximity_service.requests,
                "get",
                side_effect=[
                    proximity_service.requests.exceptions.SSLError("TLS incompatible"),
                    reponse_open_data,
                ],
            ),
        ):
            resultat = proximity_service.chercher_transports_idfm(
                48.857919,
                2.277151,
            )

        self.assertEqual(len(resultat), 1)
        self.assertEqual(resultat[0]["nom"], "La Muette")
        self.assertEqual(resultat[0]["modes"], ["Metro"])
        self.assertEqual(resultat[0]["lignes"], ["9"])
        self.assertEqual(
            resultat[0]["source"],
            "Île-de-France Mobilités - Open Data",
        )

    def test_overpass_normalise_commerce_ecole_et_sante(self):
        reponse_overpass = Mock()
        reponse_overpass.raise_for_status.return_value = None
        reponse_overpass.json.return_value = {
            "elements": [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 48.8580,
                    "lon": 2.2772,
                    "tags": {"name": "Boulangerie Test", "shop": "bakery"},
                },
                {
                    "type": "way",
                    "id": 2,
                    "center": {"lat": 48.8582, "lon": 2.2774},
                    "tags": {"name": "École Test", "amenity": "school"},
                },
                {
                    "type": "node",
                    "id": 3,
                    "lat": 48.8583,
                    "lon": 2.2775,
                    "tags": {"name": "Pharmacie Test", "amenity": "pharmacy"},
                },
            ]
        }

        with patch.object(
            proximity_service.requests,
            "post",
            return_value=reponse_overpass,
        ) as post:
            resultat = proximity_service.chercher_equipements_overpass(
                48.857919,
                2.277151,
            )

        self.assertEqual(
            {lieu["categorie"] for lieu in resultat},
            {"commerce", "education", "sante"},
        )
        self.assertTrue(all(lieu["distance_metres"] >= 0 for lieu in resultat))
        self.assertEqual(post.call_args.kwargs["headers"]["User-Agent"], "immobilier-paris-ia/1.0")
        self.assertIn("around:500", post.call_args.kwargs["data"]["data"])

    def test_analyse_proximite_continue_si_un_service_est_indisponible(self):
        equipements = [
            {"categorie": "commerce"},
            {"categorie": "education"},
            {"categorie": "sante"},
        ]
        with (
            patch.object(
                proximity_service,
                "chercher_transports_idfm",
                side_effect=HTTPException(status_code=503, detail="IDFM indisponible"),
            ),
            patch.object(
                proximity_service,
                "chercher_equipements_overpass",
                return_value=equipements,
            ),
        ):
            resultat = proximity_service.analyser_proximite(48.857919, 2.277151)

        self.assertEqual(resultat["transports"], [])
        self.assertEqual(resultat["equipements"], equipements)
        self.assertEqual(resultat["erreurs"], ["IDFM indisponible"])
        self.assertEqual(
            resultat["totaux"],
            {"transports": 0, "commerces": 1, "education": 1, "sante": 1},
        )

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
        self.assertEqual(payload["data"][0]["score_arrondissement_sur_10"], 10.0)
        self.assertEqual(
            payload["data"][0]["score_proximite_quotidienne_sur_10"],
            10.0,
        )

    def test_score_arrondissement_applique_les_ponderations(self):
        reponse_api = Mock()
        reponse_api.raise_for_status.return_value = None
        reponse_api.json.return_value = {
            "results": [
                {
                    "departement_commune": 75101,
                    "population_2010": 10000,
                    "supermarche": 10,
                    "superette": 100,
                    "fleuriste": 50,
                },
                {
                    "departement_commune": 75102,
                    "population_2010": 10000,
                    "superette": 50,
                    "fleuriste": 50,
                },
            ]
        }

        commerces_service.charger_commerces_paris.cache_clear()
        with patch.object(commerces_service.requests, "get", return_value=reponse_api):
            commerces = commerces_service.charger_commerces_paris()
        commerces_service.charger_commerces_paris.cache_clear()

        premier, second = commerces
        self.assertEqual(premier["score_proximite_quotidienne_sur_10"], 10.0)
        self.assertEqual(premier["score_diversite_commerciale_sur_10"], 7.0)
        self.assertEqual(premier["score_grandes_surfaces_sur_10"], 10.0)
        self.assertEqual(premier["score_arrondissement_sur_10"], 9.0)
        self.assertEqual(second["score_proximite_quotidienne_sur_10"], 4.0)
        self.assertEqual(second["score_diversite_commerciale_sur_10"], 7.0)
        self.assertEqual(second["score_grandes_surfaces_sur_10"], 4.0)
        self.assertEqual(second["score_arrondissement_sur_10"], 5.1)


if __name__ == "__main__":
    unittest.main()

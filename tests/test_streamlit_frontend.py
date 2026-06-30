from __future__ import annotations

# C18 : ce fichier est lance dans la CI pour verifier une partie du frontend.
# C19 : la livraison le relance pour eviter de publier une interface cassee.

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "streamlit"))
os.environ["API_KEY"] = "test-api-key"

from frontend import api_client  # noqa: E402
from frontend.formatting import (  # noqa: E402
    formater_date,
    formater_decimal,
    formater_entier,
    formater_euros,
)
from frontend.views import listings, location_rating, prediction  # noqa: E402


class TestStreamlitFrontend(unittest.TestCase):
    """Tests C17/C18 sur le client API Streamlit et l'affichage HTML."""

    def test_formatage_prepare_les_valeurs_affichees(self):
        # C17 : les valeurs doivent etre lisibles dans l'interface.
        self.assertEqual(formater_entier(12345.6), "12 346")
        self.assertEqual(formater_euros(350000), "350 000 \u20ac")
        self.assertEqual(formater_decimal(7.25, "/10"), "7,2/10")
        self.assertEqual(formater_date("2026-06-25T21:18:23"), "25/06/2026")
        self.assertEqual(formater_entier(None), "\u2014")

    def test_headers_streamlit_ajoutent_token_utilisateur(self):
        # C17 : Streamlit ajoute le token JWT quand l'utilisateur est connecte.
        with (
            patch.object(api_client, "headers_api", return_value={"X-API-Key": "test-key"}),
            patch.object(
                api_client.st,
                "session_state",
                {"auth_token": "jwt-test-token"},
            ),
        ):
            headers = api_client._headers_api()

        self.assertEqual(headers["X-API-Key"], "test-key")
        self.assertEqual(headers["Authorization"], "Bearer jwt-test-token")

    def test_api_get_json_nettoie_les_parametres_et_retourne_json(self):
        # C17 : les parametres vides ne sont pas envoyes a l'API.
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"status": "ok"}

        with (
            patch.object(
                api_client,
                "_headers_api",
                return_value={"X-API-Key": "test-key"},
            ),
            patch.object(api_client.requests, "get", return_value=response) as get,
        ):
            resultat = api_client.api_get_json(
                "/health",
                {"arrondissement": 11, "vide": None},
                arreter_sur_erreur=False,
            )

        self.assertEqual(resultat, {"status": "ok"})
        get.assert_called_once_with(
            f"{api_client.API_BASE_URL}/health",
            params={"arrondissement": 11},
            headers={"X-API-Key": "test-key"},
            timeout=60,
        )

    def test_api_get_json_transforme_les_erreurs_validation(self):
        response = Mock()
        response.status_code = 422
        response.json.return_value = {
            "detail": [
                {
                    "loc": ["body", "surface"],
                    "msg": "Input should be greater than 0",
                }
            ]
        }
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )

        with (
            patch.object(api_client, "_headers_api", return_value={}),
            patch.object(api_client.requests, "get", return_value=response),
        ):
            with self.assertRaises(api_client.ErreurApi) as contexte:
                api_client.api_get_json("/prediction/prix", arreter_sur_erreur=False)

        self.assertEqual(contexte.exception.path, "/prediction/prix")
        self.assertEqual(contexte.exception.status_code, 422)
        self.assertIn("body.surface", contexte.exception.message)

    def test_api_post_json_envoie_la_prediction_a_l_api(self):
        # C10 : le frontend doit envoyer le payload vers l'endpoint de prediction.
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"prix_estime": 465328.0}
        payload = {
            "surface": 45,
            "nombre_pieces": 2,
            "arrondissement": 11,
        }

        with (
            patch.object(
                api_client,
                "_headers_api",
                return_value={"X-API-Key": "test-key"},
            ),
            patch.object(api_client.requests, "post", return_value=response) as post,
        ):
            resultat = api_client.api_post_json(
                "/prediction/prix",
                payload,
                arreter_sur_erreur=False,
            )

        self.assertEqual(resultat, {"prix_estime": 465328.0})
        post.assert_called_once_with(
            f"{api_client.API_BASE_URL}/prediction/prix",
            json=payload,
            headers={"X-API-Key": "test-key"},
            timeout=120,
        )

    def test_cartes_html_echappent_les_donnees_utilisateur(self):
        # C17 : les textes utilisateur sont echappes avant affichage HTML.
        html_prediction = prediction._carte_prediction_historique(
            {
                "arrondissement": "<11>",
                "created_at": "2026-06-25",
                "predicted_price": 450000,
                "surface": 45,
                "nb_pieces": 2,
            }
        )
        self.assertIn("Paris &lt;11&gt;", html_prediction)
        self.assertIn("450 000 \u20ac", html_prediction)
        self.assertIn("10 000 \u20ac", html_prediction)

        html_annonce = listings._carte_annonce(
            pd.Series(
                {
                    "source": "orpi",
                    "type": "<script>",
                    "arrondissement": 11,
                    "date_scraping": "2026-06-25",
                    "prix": 350000,
                    "surface": 35,
                    "nb_pieces": 2,
                    "prix_m2": 10000,
                }
            )
        )
        self.assertIn("Orpi", html_annonce)
        self.assertIn("&lt;script&gt;", html_annonce)
        self.assertIn("350 000 \u20ac", html_annonce)

        html_adresse = location_rating._carte_adresse_historique(
            {
                "address": "<b>71 rue de Passy</b>",
                "created_at": "2026-06-25",
                "latitude": 48.857919,
                "longitude": 2.277151,
            }
        )
        self.assertIn("&lt;b&gt;71 rue de Passy&lt;/b&gt;", html_adresse)
        self.assertIn("48.85792", html_adresse)
        self.assertIn("2.27715", html_adresse)


if __name__ == "__main__":
    unittest.main()

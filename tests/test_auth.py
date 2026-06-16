from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from api import main  # noqa: E402
from api.routers import auth as auth_router  # noqa: E402
from api.services import auth as auth_service  # noqa: E402


client = TestClient(main.app)


class TestInscription(unittest.TestCase):
    def test_inscription_cree_un_utilisateur_simple(self):
        utilisateur = {
            "id": 1,
            "email": "test@example.com",
            "first_name": "Malek",
            "last_name": "Silarbi",
            "role": "user",
            "created_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
        }

        with patch.object(
            auth_router,
            "creer_utilisateur",
            return_value=utilisateur,
        ) as creer_utilisateur:
            response = client.post(
                "/auth/register",
                json={
                    "email": " Test@Example.com ",
                    "password": "mot-de-passe-solide",
                    "first_name": " Malek ",
                    "last_name": " Silarbi ",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "test@example.com")
        self.assertEqual(response.json()["role"], "user")
        self.assertNotIn("password", response.json())
        self.assertNotIn("password_hash", response.json())
        creer_utilisateur.assert_called_once_with(
            email="test@example.com",
            password="mot-de-passe-solide",
            first_name="Malek",
            last_name="Silarbi",
        )

    def test_inscription_refuse_un_mot_de_passe_trop_court(self):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "court"},
        )

        self.assertEqual(response.status_code, 422)

    def test_inscription_refuse_le_choix_du_role_admin(self):
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "mot-de-passe-solide",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_inscription_refuse_un_email_deja_utilise(self):
        with patch.object(
            auth_router,
            "creer_utilisateur",
            side_effect=HTTPException(
                status_code=409,
                detail="Un compte existe déjà avec cette adresse email.",
            ),
        ):
            response = client.post(
                "/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "mot-de-passe-solide",
                },
            )

        self.assertEqual(response.status_code, 409)

    def test_mot_de_passe_est_hache_et_verifiable(self):
        password = "mot-de-passe-solide"

        password_hash = auth_service.hacher_mot_de_passe(password)

        self.assertNotEqual(password_hash, password)
        self.assertTrue(auth_service.verifier_mot_de_passe(password, password_hash))
        self.assertFalse(
            auth_service.verifier_mot_de_passe("mauvais-mot-de-passe", password_hash)
        )


class TestConnexion(unittest.TestCase):
    def test_connexion_retourne_un_token_et_utilisateur(self):
        resultat = {
            "access_token": "jwt-test",
            "token_type": "bearer",
            "expires_in": 1800,
            "utilisateur": {
                "id": 1,
                "email": "test@example.com",
                "first_name": "Malek",
                "last_name": "Silarbi",
                "role": "user",
                "created_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
            },
        }

        with patch.object(
            auth_router,
            "connecter_utilisateur",
            return_value=resultat,
        ) as connecter_utilisateur:
            response = client.post(
                "/auth/login",
                json={
                    "email": " Test@Example.com ",
                    "password": "mot-de-passe-solide",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["access_token"], "jwt-test")
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertEqual(response.json()["expires_in"], 1800)
        self.assertEqual(response.json()["utilisateur"]["role"], "user")
        connecter_utilisateur.assert_called_once_with(
            email="test@example.com",
            password="mot-de-passe-solide",
        )

    def test_connexion_refuse_de_mauvais_identifiants(self):
        with patch.object(
            auth_router,
            "connecter_utilisateur",
            side_effect=HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect.",
            ),
        ):
            response = client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "incorrect"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Email ou mot de passe incorrect.")

    def test_token_jwt_contient_identifiant_et_role(self):
        secret = "secret-de-test-jwt-avec-32-caracteres-minimum"
        utilisateur = {
            "id": 42,
            "email": "test@example.com",
            "role": "user",
        }

        with (
            patch.dict(os.environ, {"JWT_SECRET_KEY": secret}),
            patch.object(auth_service, "charger_env"),
        ):
            token, expiration = auth_service.creer_token_acces(utilisateur)
            payload = auth_service.jwt.decode(
                token,
                secret,
                algorithms=[auth_service.JWT_ALGORITHM],
            )

        self.assertEqual(expiration, 1800)
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["role"], "user")


class TestUtilisateurConnecte(unittest.TestCase):
    def tearDown(self):
        main.app.dependency_overrides.clear()

    def test_me_retourne_le_profil_connecte(self):
        utilisateur = {
            "id": 1,
            "email": "test@example.com",
            "first_name": "Malek",
            "last_name": "Silarbi",
            "role": "user",
            "created_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
        }
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: utilisateur
        )

        response = client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "test@example.com")
        self.assertEqual(response.json()["role"], "user")

    def test_me_refuse_une_requete_sans_token(self):
        response = client.get("/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Jeton manquant.")

    def test_me_refuse_un_token_invalide(self):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer jeton-invalide"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Jeton invalide.")

    def test_decodeur_refuse_un_token_expire(self):
        secret = "secret-de-test-jwt-avec-32-caracteres-minimum"
        token = auth_service.jwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            secret,
            algorithm=auth_service.JWT_ALGORITHM,
        )

        with (
            patch.dict(os.environ, {"JWT_SECRET_KEY": secret}),
            patch.object(auth_service, "charger_env"),
            self.assertRaises(HTTPException) as contexte,
        ):
            auth_service.decoder_token_acces(token)

        self.assertEqual(contexte.exception.status_code, 401)
        self.assertEqual(contexte.exception.detail, "Le jeton a expiré.")

    def test_logout_confirme_la_deconnexion_si_token_valide(self):
        utilisateur = {
            "id": 1,
            "email": "test@example.com",
            "first_name": "Malek",
            "last_name": "Silarbi",
            "role": "user",
            "created_at": datetime(2026, 6, 15, tzinfo=timezone.utc),
        }
        main.app.dependency_overrides[auth_service.obtenir_utilisateur_courant] = (
            lambda: utilisateur
        )

        response = client.post("/auth/logout")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Déconnexion réussie.")


if __name__ == "__main__":
    unittest.main()

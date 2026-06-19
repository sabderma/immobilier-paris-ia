from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from typing import Any, Optional

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from api.core import charger_env, engine


password_hasher = PasswordHasher()
bearer_scheme = HTTPBearer(auto_error=False)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30
ROLES_ADMIN = {"admin", "super_admin"}


def hacher_mot_de_passe(password: str) -> str:
    """Hache un mot de passe avant son enregistrement en base."""
    return password_hasher.hash(password)


def verifier_mot_de_passe(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe sans jamais le comparer en clair."""
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


def obtenir_cle_jwt() -> str:
    """Retourne la clé JWT configurée sur le serveur."""
    charger_env()
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé JWT du serveur n'est pas configurée.",
        )
    return secret


def creer_token_acces(utilisateur: dict[str, Any]) -> tuple[str, int]:
    """Crée un jeton JWT temporaire pour un utilisateur connecté."""
    secret = obtenir_cle_jwt()

    expiration_secondes = JWT_EXPIRATION_MINUTES * 60
    maintenant = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(utilisateur["id"]),
            "email": utilisateur["email"],
            "role": utilisateur["role"],
            "iat": maintenant,
            "exp": maintenant + timedelta(seconds=expiration_secondes),
        },
        secret,
        algorithm=JWT_ALGORITHM,
    )
    return token, expiration_secondes


def decoder_token_acces(token: str) -> dict[str, Any]:
    """Valide un JWT et retourne ses informations."""
    try:
        return jwt.decode(
            token,
            obtenir_cle_jwt(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le jeton a expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def obtenir_utilisateur_courant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Retourne l'utilisateur actif identifié par le jeton Bearer."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decoder_token_acces(credentials.credentials)
    return obtenir_utilisateur_depuis_payload(payload)


def obtenir_admin_courant(
    utilisateur: dict[str, Any] = Depends(obtenir_utilisateur_courant),
) -> dict[str, Any]:
    """Autorise uniquement les utilisateurs ayant un rôle d'administration."""
    if utilisateur["role"] not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    return utilisateur


def obtenir_utilisateur_optionnel(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict[str, Any]]:
    """Retourne l'utilisateur connecté si un jeton Bearer est envoyé."""
    if credentials is None:
        return None

    payload = decoder_token_acces(credentials.credentials)
    return obtenir_utilisateur_depuis_payload(payload)


def obtenir_utilisateur_depuis_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Recharge l'utilisateur depuis PostgreSQL à partir du payload JWT."""
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    with engine.connect() as connexion:
        utilisateur = connexion.execute(
            text(
                """
                SELECT id, email, first_name, last_name, role, is_active, created_at
                FROM users
                WHERE id = :user_id
                LIMIT 1;
                """
            ),
            {"user_id": user_id},
        ).mappings().one_or_none()

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not utilisateur["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    return {
        cle: utilisateur[cle]
        for cle in ["id", "email", "first_name", "last_name", "role", "created_at"]
    }


def mettre_a_jour_profil_utilisateur(
    *,
    user_id: int,
    first_name: Optional[str],
    last_name: Optional[str],
) -> dict[str, Any]:
    """Modifie le prénom et le nom de l'utilisateur connecté."""
    with engine.begin() as connexion:
        utilisateur = connexion.execute(
            text(
                """
                UPDATE users
                SET
                    first_name = :first_name,
                    last_name = :last_name,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
                RETURNING id, email, first_name, last_name, role, created_at;
                """
            ),
            {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
            },
        ).mappings().one_or_none()

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    return dict(utilisateur)


def changer_mot_de_passe_utilisateur(
    *,
    user_id: int,
    current_password: str,
    new_password: str,
) -> None:
    """Remplace le mot de passe après vérification du mot de passe actuel."""
    with engine.connect() as connexion:
        utilisateur = connexion.execute(
            text(
                """
                SELECT password_hash
                FROM users
                WHERE id = :user_id
                  AND is_active = TRUE
                LIMIT 1;
                """
            ),
            {"user_id": user_id},
        ).mappings().one_or_none()

    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    if not verifier_mot_de_passe(current_password, utilisateur["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe actuel incorrect.",
        )

    with engine.begin() as connexion:
        connexion.execute(
            text(
                """
                UPDATE users
                SET
                    password_hash = :password_hash,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id;
                """
            ),
            {
                "user_id": user_id,
                "password_hash": hacher_mot_de_passe(new_password),
            },
        )


def connecter_utilisateur(*, email: str, password: str) -> dict[str, Any]:
    """Vérifie les identifiants puis retourne l'utilisateur et son JWT."""
    with engine.connect() as connexion:
        utilisateur = connexion.execute(
            text(
                """
                SELECT
                    id,
                    email,
                    password_hash,
                    first_name,
                    last_name,
                    role,
                    is_active,
                    created_at
                FROM users
                WHERE LOWER(email) = LOWER(:email)
                LIMIT 1;
                """
            ),
            {"email": email},
        ).mappings().one_or_none()

    if utilisateur is None or not verifier_mot_de_passe(
        password,
        utilisateur["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    if not utilisateur["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    utilisateur_public = {
        cle: utilisateur[cle]
        for cle in ["id", "email", "first_name", "last_name", "role", "created_at"]
    }
    token, expiration_secondes = creer_token_acces(utilisateur_public)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expiration_secondes,
        "utilisateur": utilisateur_public,
    }


def creer_utilisateur(
    *,
    email: str,
    password: str,
    first_name: str | None,
    last_name: str | None,
) -> dict[str, Any]:
    """Crée un compte utilisateur avec le rôle user imposé côté serveur."""
    params = {
        "email": email,
        "password_hash": hacher_mot_de_passe(password),
        "first_name": first_name,
        "last_name": last_name,
    }

    try:
        with engine.begin() as connexion:
            utilisateur = connexion.execute(
                text(
                    """
                    INSERT INTO users (email, password_hash, first_name, last_name, role)
                    VALUES (:email, :password_hash, :first_name, :last_name, 'user')
                    RETURNING id, email, first_name, last_name, role, created_at;
                    """
                ),
                params,
            ).mappings().one()
    except IntegrityError as exc:
        if getattr(exc.orig, "pgcode", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un compte existe déjà avec cette adresse email.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les informations utilisateur sont invalides.",
        ) from exc

    return dict(utilisateur)

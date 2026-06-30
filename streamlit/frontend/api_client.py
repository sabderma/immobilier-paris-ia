"""Client HTTP Streamlit utilise pour integrer l'API FastAPI en C17.

Ce fichier evite de repeter les appels `requests` dans chaque page Streamlit.
Il ajoute les bons headers et transforme les erreurs API en messages lisibles.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import streamlit as st

from frontend.config import API_BASE_URL, API_ENDPOINTS, headers_api


class ErreurApi(RuntimeError):
    def __init__(
        self,
        path: str,
        message: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.path = path
        self.message = message
        self.status_code = status_code


def tuple_params(params: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Transforme les filtres en tuple stable pour le cache Streamlit."""
    return tuple(sorted((k, v) for k, v in params.items() if v is not None))


def _headers_api() -> dict[str, str]:
    """Ajoute la cle API et le token utilisateur si l'utilisateur est connecte."""
    headers = headers_api()
    token = st.session_state.get("auth_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _message_validation(detail: list[Any]) -> str:
    messages = []
    for erreur in detail:
        if not isinstance(erreur, dict):
            messages.append(str(erreur))
            continue
        champ = ".".join(str(partie) for partie in erreur.get("loc", []) if partie)
        message = erreur.get("msg") or "Erreur de validation"
        messages.append(f"{champ} : {message}" if champ else str(message))
    return " ; ".join(messages)


def _message_erreur_api(response: requests.Response) -> str:
    """Recupere le message d'erreur renvoye par FastAPI."""
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text

    if isinstance(detail, list):
        return _message_validation(detail)
    if detail:
        return str(detail)
    return f"Erreur HTTP {response.status_code}"


def _gerer_erreur_api(
    path: str,
    message: str,
    *,
    arreter_sur_erreur: bool,
    status_code: int | None = None,
) -> None:
    if arreter_sur_erreur:
        st.error(f"Erreur API sur {path} : {message}")
        st.stop()
    raise ErreurApi(path=path, message=message, status_code=status_code)


def api_get_json(
    path: str,
    params: dict[str, Any] | None = None,
    *,
    arreter_sur_erreur: bool = True,
) -> Any:
    """Appelle une route GET JSON de FastAPI."""
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=_headers_api(),
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        response = exc.response
        message = _message_erreur_api(response) if response is not None else str(exc)
        _gerer_erreur_api(
            path,
            message,
            arreter_sur_erreur=arreter_sur_erreur,
            status_code=response.status_code if response is not None else None,
        )
    except requests.exceptions.RequestException as exc:
        _gerer_erreur_api(
            path,
            str(exc),
            arreter_sur_erreur=arreter_sur_erreur,
        )


def api_get_csv(
    path: str,
    params: dict[str, Any] | None = None,
    *,
    arreter_sur_erreur: bool = True,
) -> bytes:
    """Recupere un fichier CSV renvoye par l'API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=_headers_api(),
            timeout=120,
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as exc:
        response = exc.response
        message = _message_erreur_api(response) if response is not None else str(exc)
        _gerer_erreur_api(
            path,
            message,
            arreter_sur_erreur=arreter_sur_erreur,
            status_code=response.status_code if response is not None else None,
        )
    except requests.exceptions.RequestException as exc:
        _gerer_erreur_api(
            path,
            str(exc),
            arreter_sur_erreur=arreter_sur_erreur,
        )


def api_post_json(
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    arreter_sur_erreur: bool = True,
) -> Any:
    """Envoie un POST JSON a l'API, par exemple prediction ou connexion."""
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            json=payload or {},
            headers=_headers_api(),
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        response = exc.response
        message = _message_erreur_api(response) if response is not None else str(exc)
        _gerer_erreur_api(
            path,
            message,
            arreter_sur_erreur=arreter_sur_erreur,
            status_code=response.status_code if response is not None else None,
        )
    except requests.exceptions.RequestException as exc:
        _gerer_erreur_api(
            path,
            str(exc),
            arreter_sur_erreur=arreter_sur_erreur,
        )


def api_patch_json(
    path: str,
    payload: dict[str, Any],
    *,
    arreter_sur_erreur: bool = True,
) -> Any:
    """Envoie une modification partielle vers l'API."""
    try:
        response = requests.patch(
            f"{API_BASE_URL}{path}",
            json=payload,
            headers=_headers_api(),
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        response = exc.response
        message = _message_erreur_api(response) if response is not None else str(exc)
        _gerer_erreur_api(
            path,
            message,
            arreter_sur_erreur=arreter_sur_erreur,
            status_code=response.status_code if response is not None else None,
        )
    except requests.exceptions.RequestException as exc:
        _gerer_erreur_api(
            path,
            str(exc),
            arreter_sur_erreur=arreter_sur_erreur,
        )


def api_delete(
    path: str,
    *,
    arreter_sur_erreur: bool = True,
) -> None:
    """Supprime une ressource cote API."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}{path}",
            headers=_headers_api(),
            timeout=60,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        response = exc.response
        message = _message_erreur_api(response) if response is not None else str(exc)
        _gerer_erreur_api(
            path,
            message,
            arreter_sur_erreur=arreter_sur_erreur,
            status_code=response.status_code if response is not None else None,
        )
    except requests.exceptions.RequestException as exc:
        _gerer_erreur_api(
            path,
            str(exc),
            arreter_sur_erreur=arreter_sur_erreur,
        )


@st.cache_data(ttl=300, show_spinner=False)
def charger_filtres() -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["filtres"])


@st.cache_data(ttl=120, show_spinner=False)
def charger_stats_arrondissements(params: tuple[tuple[str, Any], ...]) -> list[dict]:
    return api_get_json(API_ENDPOINTS["stats_arrondissements"], dict(params))


@st.cache_data(ttl=120, show_spinner=False)
def charger_resume(params: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["resume"], dict(params))


@st.cache_data(ttl=120, show_spinner=False)
def charger_evolution(params: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    df = pd.DataFrame(api_get_json(API_ENDPOINTS["evolution"], dict(params)))
    if not df.empty:
        df["mois"] = pd.to_datetime(df["mois"])
    return df


@st.cache_data(ttl=120, show_spinner=False)
def charger_distribution(params: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    return pd.DataFrame(api_get_json(API_ENDPOINTS["distribution"], dict(params)))


@st.cache_data(ttl=3600, show_spinner=False)
def charger_points(params: tuple[tuple[str, Any], ...]) -> pd.DataFrame:
    payload = api_get_json(API_ENDPOINTS["points"], dict(params))
    return pd.DataFrame(payload.get("data", []))


@st.cache_data(ttl=300, show_spinner=False)
def charger_csv(params: tuple[tuple[str, Any], ...]) -> bytes:
    return api_get_csv(API_ENDPOINTS["csv"], dict(params))


@st.cache_data(ttl=300, show_spinner=False)
def charger_filtres_scraping() -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["scraping_filtres"])


@st.cache_data(ttl=120, show_spinner=False)
def charger_annonces_scraping(
    params: tuple[tuple[str, Any], ...],
) -> tuple[pd.DataFrame, int]:
    payload = api_get_json(API_ENDPOINTS["scraping_annonces"], dict(params))
    return pd.DataFrame(payload.get("data", [])), int(payload.get("nombre_total", 0))


@st.cache_data(ttl=120, show_spinner=False)
def charger_resume_scraping(params: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["scraping_resume"], dict(params))


@st.cache_data(ttl=120, show_spinner=False)
def charger_stats_scraping_arrondissements(
    params: tuple[tuple[str, Any], ...],
) -> pd.DataFrame:
    return pd.DataFrame(
        api_get_json(API_ENDPOINTS["scraping_arrondissements"], dict(params))
    )


@st.cache_data(ttl=120, show_spinner=False)
def charger_stats_scraping_sources(
    params: tuple[tuple[str, Any], ...],
) -> pd.DataFrame:
    return pd.DataFrame(api_get_json(API_ENDPOINTS["scraping_sources"], dict(params)))


@st.cache_data(ttl=120, show_spinner=False)
def charger_distribution_scraping(
    params: tuple[tuple[str, Any], ...],
) -> pd.DataFrame:
    return pd.DataFrame(api_get_json(API_ENDPOINTS["scraping_distribution"], dict(params)))


@st.cache_data(ttl=120, show_spinner=False)
def charger_comparaison_scraping_dvf_2025(
    params: tuple[tuple[str, Any], ...],
) -> pd.DataFrame:
    return pd.DataFrame(
        api_get_json(API_ENDPOINTS["scraping_comparaison_2025"], dict(params))
    )


@st.cache_data(ttl=300, show_spinner=False)
def charger_commerces_paris() -> pd.DataFrame:
    payload = api_get_json(API_ENDPOINTS["commerces"])
    commerces = pd.DataFrame(payload.get("data", []))
    return commerces


def geocoder_adresse(adresse: str) -> dict[str, Any]:
    """Envoie l'adresse saisie a l'API de geocodage."""
    return api_post_json(
        API_ENDPOINTS["adresse_geocodage"],
        {"adresse": adresse},
    )


def charger_admin_overview() -> dict[str, Any]:
    return api_get_json(API_ENDPOINTS["admin_overview"])


def charger_admin_users(limit: int = 100) -> pd.DataFrame:
    return pd.DataFrame(api_get_json(API_ENDPOINTS["admin_users"], {"limit": limit}))


def charger_admin_predictions(limit: int = 100) -> pd.DataFrame:
    return pd.DataFrame(
        api_get_json(API_ENDPOINTS["admin_predictions"], {"limit": limit})
    )


def charger_admin_addresses(limit: int = 100) -> pd.DataFrame:
    return pd.DataFrame(api_get_json(API_ENDPOINTS["admin_addresses"], {"limit": limit}))


def modifier_role_admin_user(user_id: int, role: str) -> dict[str, Any]:
    """Demande a l'API de modifier le role d'un utilisateur."""
    return api_patch_json(
        f"{API_ENDPOINTS['admin_users']}/{user_id}/role",
        {"role": role},
        arreter_sur_erreur=False,
    )


def supprimer_admin_user(user_id: int) -> None:
    """Demande a l'API de supprimer un utilisateur depuis l'admin."""
    api_delete(
        f"{API_ENDPOINTS['admin_users']}/{user_id}",
        arreter_sur_erreur=False,
    )

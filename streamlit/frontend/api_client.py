from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import streamlit as st

from frontend.config import API_BASE_URL, API_ENDPOINTS, headers_api


def tuple_params(params: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(sorted((k, v) for k, v in params.items() if v is not None))


def api_get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=headers_api(),
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        detail = None
        response = exc.response
        if response is not None:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = response.text
        message = detail or str(exc)
        st.error(f"Erreur API sur {path} : {message}")
        st.stop()
    except requests.exceptions.RequestException as exc:
        st.error(f"Erreur API sur {path} : {exc}")
        st.stop()


def api_get_csv(path: str, params: dict[str, Any] | None = None) -> bytes:
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=headers_api(),
            timeout=120,
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as exc:
        detail = None
        response = exc.response
        if response is not None:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = response.text
        message = detail or str(exc)
        st.error(f"Erreur API sur {path} : {message}")
        st.stop()
    except requests.exceptions.RequestException as exc:
        st.error(f"Erreur API sur {path} : {exc}")
        st.stop()


def api_post_json(path: str, payload: dict[str, Any]) -> Any:
    try:
        response = requests.post(
            f"{API_BASE_URL}{path}",
            json=payload,
            headers=headers_api(),
            timeout=120,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        detail = None
        response = exc.response
        if response is not None:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = response.text
        message = detail or str(exc)
        st.error(f"Erreur API sur {path} : {message}")
        st.stop()
    except requests.exceptions.RequestException as exc:
        st.error(f"Erreur API sur {path} : {exc}")
        st.stop()


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


@st.cache_data(ttl=3600, show_spinner=False)
def charger_commerces_paris() -> pd.DataFrame:
    payload = api_get_json(API_ENDPOINTS["commerces"])
    return pd.DataFrame(payload.get("data", []))


def noter_adresse_gemini(adresse: str) -> dict[str, Any]:
    return api_post_json(
        API_ENDPOINTS["adresse_score"],
        {"adresse": adresse},
    )

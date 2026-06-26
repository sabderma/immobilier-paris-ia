from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from frontend.api_client import ErreurApi, api_patch_json, api_post_json
from frontend.config import API_ENDPOINTS


def utilisateur_connecte() -> dict[str, Any] | None:
    token = st.session_state.get("auth_token")
    utilisateur = st.session_state.get("auth_user")
    return utilisateur if token and utilisateur else None


def _connecter_session(payload_connexion: dict[str, Any]) -> None:
    st.session_state["auth_token"] = payload_connexion["access_token"]
    st.session_state["auth_user"] = payload_connexion["utilisateur"]


def _vider_session_utilisateur() -> None:
    for cle in (
        "auth_token",
        "auth_user",
        "resultat_geocodage_adresse",
        "arrondissement_note",
    ):
        st.session_state.pop(cle, None)


def _nom_affiche(utilisateur: dict[str, Any]) -> str:
    prenom = utilisateur.get("first_name") or ""
    nom = utilisateur.get("last_name") or ""
    nom_complet = f"{prenom} {nom}".strip()
    return nom_complet or utilisateur.get("email", "Mon compte")


def _formulaire_connexion() -> None:
    with st.form("formulaire_connexion_utilisateur"):
        email = st.text_input("Email", placeholder="exemple@mail.com")
        password = st.text_input("Mot de passe", type="password")
        soumis = st.form_submit_button("Se connecter", width="stretch")

    if not soumis:
        return

    if not email.strip() or not password:
        st.error("Renseigne ton email et ton mot de passe.")
        return

    try:
        payload = api_post_json(
            API_ENDPOINTS["auth_login"],
            {"email": email.strip(), "password": password},
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.error(exc.message)
        return

    _connecter_session(payload)
    st.rerun()


def _formulaire_inscription() -> None:
    with st.form("formulaire_inscription_utilisateur"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Prénom")
        with col2:
            last_name = st.text_input("Nom")

        email = st.text_input("Email", placeholder="exemple@mail.com")
        password = st.text_input("Mot de passe", type="password")
        password_confirmation = st.text_input(
            "Confirmer le mot de passe",
            type="password",
        )
        soumis = st.form_submit_button("Créer mon compte", width="stretch")

    if not soumis:
        return

    if not email.strip() or not password:
        st.error("Renseigne au minimum ton email et ton mot de passe.")
        return
    if password != password_confirmation:
        st.error("Les deux mots de passe ne sont pas identiques.")
        return
    if len(password) < 8:
        st.error("Le mot de passe doit contenir au moins 8 caractères.")
        return

    payload_inscription = {
        "email": email.strip(),
        "password": password,
        "first_name": first_name.strip() or None,
        "last_name": last_name.strip() or None,
    }

    try:
        api_post_json(
            API_ENDPOINTS["auth_register"],
            payload_inscription,
            arreter_sur_erreur=False,
        )
        payload_connexion = api_post_json(
            API_ENDPOINTS["auth_login"],
            {"email": email.strip(), "password": password},
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.error(exc.message)
        return

    _connecter_session(payload_connexion)
    st.rerun()


def afficher_page_authentification() -> None:
    st.markdown(
        """
        <div class="auth-shell">
            <div class="auth-badge">DVF Vision Paris</div>
            <h1>Explorateur de données de valeurs foncières</h1>
            <p>
                Suivez l’évolution des prix de l’immobilier et trouvez le prix
                des ventes immobilières des 5 dernières années et les
                appartements disponibles.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, centre, _ = st.columns([0.22, 0.56, 0.22])
    with centre:
        with st.container(border=True):
            onglet_connexion, onglet_inscription = st.tabs(
                ["Connexion", "Inscription"]
            )
            with onglet_connexion:
                _formulaire_connexion()
            with onglet_inscription:
                _formulaire_inscription()

    st.markdown(
        """
        <div class="auth-rgpd-contact">
            Pour toute demande concernant vos coordonnées, vos données
            personnelles, une suppression de données ou toute autre demande,
            veuillez contacter l'adresse
            <a href="mailto:ssabderma@gmail.com">ssabderma@gmail.com</a>.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _modifier_profil(utilisateur: dict[str, Any]) -> None:
    st.markdown("##### Modifier mon profil")
    with st.form("formulaire_modifier_profil"):
        first_name = st.text_input(
            "Prénom",
            value=utilisateur.get("first_name") or "",
        )
        last_name = st.text_input(
            "Nom",
            value=utilisateur.get("last_name") or "",
        )
        soumis = st.form_submit_button("Enregistrer le profil", width="stretch")

    if not soumis:
        return

    try:
        utilisateur_modifie = api_patch_json(
            API_ENDPOINTS["user_profile"],
            {
                "first_name": first_name.strip() or None,
                "last_name": last_name.strip() or None,
            },
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.error(exc.message)
        return

    st.session_state["auth_user"] = utilisateur_modifie
    st.success("Profil modifié.")


def _changer_mot_de_passe() -> None:
    st.markdown("##### Changer mon mot de passe")
    with st.form("formulaire_modifier_mot_de_passe"):
        current_password = st.text_input("Mot de passe actuel", type="password")
        new_password = st.text_input("Nouveau mot de passe", type="password")
        confirmation = st.text_input(
            "Confirmer le nouveau mot de passe",
            type="password",
        )
        soumis = st.form_submit_button("Modifier le mot de passe", width="stretch")

    if not soumis:
        return

    if new_password != confirmation:
        st.error("Les deux nouveaux mots de passe ne sont pas identiques.")
        return
    if len(new_password) < 8:
        st.error("Le nouveau mot de passe doit contenir au moins 8 caractères.")
        return

    try:
        api_patch_json(
            API_ENDPOINTS["user_password"],
            {
                "current_password": current_password,
                "new_password": new_password,
            },
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.error(exc.message)
        return

    st.success("Mot de passe modifié.")


def afficher_menu_compte() -> None:
    utilisateur = utilisateur_connecte()
    if not utilisateur:
        return

    libelle = _nom_affiche(utilisateur)
    if hasattr(st, "popover"):
        conteneur_compte = st.popover(libelle, use_container_width=True)
    else:
        conteneur_compte = st.expander(libelle)

    with conteneur_compte:
        st.markdown(f"**{_nom_affiche(utilisateur)}**")
        email_affiche = utilisateur.get("email", "")
        if email_affiche == "malek@gmail.com":
            email_affiche = "maleksilarbi@gmail.com"
        st.markdown(
            f'<div class="account-email">{escape(email_affiche)}</div>',
            unsafe_allow_html=True,
        )
        st.divider()
        _modifier_profil(utilisateur)
        st.divider()
        _changer_mot_de_passe()
        st.divider()
        if st.button("Déconnexion", type="primary", width="stretch"):
            try:
                api_post_json(
                    API_ENDPOINTS["auth_logout"],
                    {},
                    arreter_sur_erreur=False,
                )
            except ErreurApi:
                pass
            _vider_session_utilisateur()
            st.rerun()

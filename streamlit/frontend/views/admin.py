from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from frontend.api_client import (
    ErreurApi,
    charger_admin_addresses,
    charger_admin_overview,
    charger_admin_predictions,
    charger_admin_users,
    modifier_role_admin_user,
    supprimer_admin_user,
)
from frontend.formatting import formater_date, formater_entier, formater_euros


ROLES = ["user", "admin"]
ROLE_SUPER_ADMIN = "super_admin"
VUES_ADMIN = [
    "Utilisateurs",
    "Historique global des prédictions",
    "Historique global des adresses exactes",
]
HAUTEUR_PANNEAU_ADMIN = 680


def _texte(valeur: object, defaut: str = "—") -> str:
    if valeur is None or pd.isna(valeur):
        return defaut
    return str(valeur)


def _html(valeur: object, defaut: str = "—") -> str:
    return escape(_texte(valeur, defaut))


def _nom_utilisateur(row: pd.Series) -> str:
    nom = f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip()
    return nom or "—"


def _afficher_tableau_vide(message: str) -> None:
    st.info(message)


def _utilisateur_connecte_id() -> int | None:
    utilisateur = st.session_state.get("auth_user") or {}
    user_id = utilisateur.get("id")
    return int(user_id) if user_id is not None else None


def _modifier_role_utilisateur(user_id: int, role: str) -> None:
    try:
        modifier_role_admin_user(user_id, role)
    except ErreurApi as exc:
        st.error(exc.message)
        return

    st.success("Rôle utilisateur modifié.")
    st.rerun()


def _supprimer_utilisateur(user_id: int) -> None:
    try:
        supprimer_admin_user(user_id)
    except ErreurApi as exc:
        st.error(exc.message)
        return

    st.success("Utilisateur supprimé.")
    st.rerun()


def afficher_gestion_utilisateurs(utilisateurs: pd.DataFrame) -> None:
    admin_id = _utilisateur_connecte_id()

    for index_utilisateur, (_, utilisateur) in enumerate(
        utilisateurs.iterrows(),
        start=1,
    ):
        user_id = int(utilisateur["id"])
        role_actuel = str(utilisateur["role"])
        est_compte_connecte = user_id == admin_id
        est_super_admin = role_actuel == ROLE_SUPER_ADMIN
        est_protege = est_compte_connecte or est_super_admin
        actif = "Oui" if bool(utilisateur.get("is_active")) else "Non"
        if est_super_admin:
            classe_role = "admin-badge-super"
        elif role_actuel == "admin":
            classe_role = "admin-badge-admin"
        else:
            classe_role = "admin-badge-user"
        classe_actif = (
            "admin-badge-active" if bool(utilisateur.get("is_active")) else "admin-badge-muted"
        )
        roles_disponibles = ROLES if role_actuel in ROLES else [role_actuel]

        with st.container(border=True, key=f"admin_user_block_{user_id}"):
            st.markdown(
                f"""
                <div class="admin-user-card">
                    <div>
                        <div class="admin-user-index">Utilisateur {index_utilisateur}</div>
                        <div class="admin-card-kicker">Compte utilisateur</div>
                        <div class="admin-card-title">{_html(utilisateur.get("email"))}</div>
                        <div class="admin-card-subtitle">{_html(_nom_utilisateur(utilisateur))}</div>
                    </div>
                    <div class="admin-badge-row">
                        <span class="admin-badge {classe_role}">{_html(role_actuel)}</span>
                        <span class="admin-badge {classe_actif}">{_html(actif)}</span>
                    </div>
                </div>
                <div class="admin-info-grid">
                    <div>
                        <span>Inscription</span>
                        <strong>{_html(formater_date(utilisateur.get("created_at")))}</strong>
                    </div>
                    <div>
                        <span>Rôle actuel</span>
                        <strong>{_html(role_actuel)}</strong>
                    </div>
                </div>
                <div class="admin-user-actions-title">Gestion du compte</div>
                """,
                unsafe_allow_html=True,
            )

            role_choisi = st.selectbox(
                "Attribuer un rôle",
                roles_disponibles,
                index=roles_disponibles.index(role_actuel),
                key=f"admin_role_{user_id}",
                disabled=est_protege,
            )
            col_save, col_delete = st.columns(2)
            if col_save.button(
                "Enregistrer",
                key=f"admin_save_role_{user_id}",
                disabled=est_protege or role_choisi == role_actuel,
                width="stretch",
            ):
                _modifier_role_utilisateur(user_id, role_choisi)

            if col_delete.button(
                "Supprimer",
                key=f"admin_delete_user_{user_id}",
                disabled=est_protege,
                width="stretch",
            ):
                _supprimer_utilisateur(user_id)

            if est_super_admin:
                st.caption(
                    "Compte super admin protégé : rôle et suppression bloqués."
                )
            elif est_compte_connecte:
                st.caption(
                    "Compte admin connecté : suppression et changement de rôle bloqués."
                )


def afficher_predictions_admin(predictions: pd.DataFrame) -> None:
    if predictions.empty:
        _afficher_tableau_vide("Aucune prédiction enregistrée.")
        return

    for _, prediction in predictions.iterrows():
        st.markdown(
            f"""
            <div class="admin-history-card">
                <div>
                    <div class="admin-card-kicker">Prix estimé</div>
                    <div class="admin-history-title">
                        {_html(formater_euros(prediction.get("predicted_price")))}
                    </div>
                    <div class="admin-chip-row">
                        <span class="admin-chip">{_html(formater_entier(prediction.get("surface")))} m²</span>
                        <span class="admin-chip">{_html(formater_entier(prediction.get("nb_pieces")))} pièce(s)</span>
                        <span class="admin-chip">Paris {_html(prediction.get("arrondissement"))}</span>
                    </div>
                </div>
                <div class="admin-history-side">
                    <span>{_html(formater_date(prediction.get("created_at")))}</span>
                    <strong>{_html(prediction.get("user_email"))}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def afficher_adresses_admin(addresses: pd.DataFrame) -> None:
    if addresses.empty:
        _afficher_tableau_vide("Aucune adresse enregistrée.")
        return

    for _, adresse in addresses.iterrows():
        st.markdown(
            f"""
            <div class="admin-history-card">
                <div>
                    <div class="admin-card-kicker">Adresse exacte</div>
                    <div class="admin-address-title">{_html(adresse.get("address"))}</div>
                    <div class="admin-chip-row">
                        <span class="admin-chip">Lat. {float(adresse.get("latitude", 0)):.5f}</span>
                        <span class="admin-chip">Long. {float(adresse.get("longitude", 0)):.5f}</span>
                    </div>
                </div>
                <div class="admin-history-side">
                    <span>{_html(formater_date(adresse.get("created_at")))}</span>
                    <strong>{_html(adresse.get("user_email"))}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def afficher_admin() -> None:
    st.markdown("### Administration")
    st.caption(
        "Espace réservé aux administrateurs : suivi des utilisateurs, "
        "des prédictions et des adresses exactes."
    )

    overview = charger_admin_overview()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Utilisateurs", formater_entier(overview.get("total_users")))
    col2.metric("Comptes actifs", formater_entier(overview.get("total_active_users")))
    col3.metric("Prédictions", formater_entier(overview.get("total_predictions")))
    col4.metric("Adresses", formater_entier(overview.get("total_addresses")))

    vue_active = st.segmented_control(
        "Vue administration",
        VUES_ADMIN,
        default=VUES_ADMIN[0],
        key="vue_admin_interne",
        label_visibility="collapsed",
        width="stretch",
    )
    vue_active = vue_active or VUES_ADMIN[0]

    with st.container(border=True, height=HAUTEUR_PANNEAU_ADMIN):
        st.markdown(f"#### {vue_active}")

        if vue_active == VUES_ADMIN[0]:
            utilisateurs = charger_admin_users()
            if utilisateurs.empty:
                _afficher_tableau_vide("Aucun utilisateur trouvé.")
            else:
                afficher_gestion_utilisateurs(utilisateurs)

        elif vue_active == VUES_ADMIN[1]:
            afficher_predictions_admin(charger_admin_predictions())

        else:
            afficher_adresses_admin(charger_admin_addresses())

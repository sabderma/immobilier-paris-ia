from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import ErreurApi, api_delete, api_get_json, api_post_json
from frontend.config import API_ENDPOINTS
from frontend.formatting import formater_date, formater_entier, formater_euros


def supprimer_prediction_historique(prediction_id: int) -> None:
    try:
        api_delete(
            f"{API_ENDPOINTS['user_predictions']}/{prediction_id}",
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.error(exc.message)
        return

    st.success("Prédiction supprimée de ton historique.")
    st.rerun()


def afficher_historique_predictions() -> None:
    st.markdown("#### Historique de mes prédictions")

    try:
        historique = api_get_json(
            API_ENDPOINTS["user_predictions"],
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.caption(f"Historique indisponible : {exc.message}")
        return

    if not historique:
        st.info("Aucune prédiction enregistrée pour le moment.")
        return

    historique_tries = sorted(
        historique,
        key=lambda ligne: ligne.get("created_at") or "",
        reverse=True,
    )

    colonnes = st.columns([0.16, 0.14, 0.12, 0.18, 0.2, 0.14])
    libelles = ["Date", "Surface", "Pièces", "Arrondissement", "Prix estimé", ""]
    for colonne, libelle in zip(colonnes, libelles):
        colonne.markdown(f"**{libelle}**")

    for ligne in historique_tries:
        prediction_id = int(ligne["id"])
        with st.container(border=True):
            (
                col_date,
                col_surface,
                col_pieces,
                col_arr,
                col_prix,
                col_action,
            ) = st.columns([0.16, 0.14, 0.12, 0.18, 0.2, 0.14])
            col_date.write(formater_date(ligne.get("created_at")))
            col_surface.write(f"{formater_entier(ligne.get('surface'))} m²")
            col_pieces.write(formater_entier(ligne.get("nb_pieces")))
            col_arr.write(f"Paris {ligne.get('arrondissement')}")
            col_prix.write(formater_euros(ligne.get("predicted_price")))
            if col_action.button(
                "Effacer",
                key=f"effacer_prediction_{prediction_id}",
                width="stretch",
            ):
                supprimer_prediction_historique(prediction_id)


def afficher_prediction(options: dict[str, Any]) -> None:
    st.markdown("### Prédire le prix d’un appartement")

    arrondissements = [int(a) for a in options.get("arrondissements", range(1, 21))]
    arrondissements = sorted(set(arrondissements))

    surface_min = max(1, int(options.get("surface_min", 10)))
    surface_max = max(surface_min, int(options.get("surface_max", 200)))
    surface_defaut = min(max(45, surface_min), surface_max)

    with st.form("formulaire_prediction_appartement"):
        col1, col2, col3 = st.columns(3)
        with col1:
            surface = st.number_input(
                "Surface de l’appartement (m²)",
                value=float(surface_defaut),
                step=1.0,
            )
        with col2:
            nombre_pieces = st.number_input(
                "Nombre de pièces",
                value=2,
                step=1,
            )
        with col3:
            arrondissement = st.selectbox(
                "Arrondissement",
                arrondissements,
                index=arrondissements.index(11) if 11 in arrondissements else 0,
                format_func=lambda valeur: f"Paris {valeur}",
            )

        soumis = st.form_submit_button("Prédire le prix")

    if not soumis:
        st.info("Renseigne les paramètres de ton appartement puis lance la prédiction.")
        afficher_historique_predictions()
        return

    erreurs_saisie = []
    if surface <= 0:
        erreurs_saisie.append("La surface doit être strictement supérieure à 0 m².")
    if nombre_pieces <= 0:
        erreurs_saisie.append("Le nombre de pièces doit être strictement supérieur à 0.")

    if erreurs_saisie:
        for erreur in erreurs_saisie:
            st.error(erreur)
        afficher_historique_predictions()
        return

    try:
        resultat_prediction = api_post_json(
            API_ENDPOINTS["prediction_prix"],
            {
                "surface": surface,
                "nombre_pieces": nombre_pieces,
                "arrondissement": arrondissement,
            },
        )
        prix_estime = float(resultat_prediction["prix_estime"])
        mae_euros = float(resultat_prediction["mae_euros"])
        prix_min_indicatif = float(resultat_prediction["prix_min_indicatif"])
        prix_max_indicatif = float(resultat_prediction["prix_max_indicatif"])
    except Exception as exc:
        st.error(f"Impossible de calculer la prédiction : {exc}")
        afficher_historique_predictions()
        return

    prix_m2 = prix_estime / surface if surface else None
    st.markdown(
        f"""
        <div class="prediction-result">
            <div class="prediction-label">Fourchette de prix indicative</div>
            <div class="prediction-price">
                {formater_euros(prix_min_indicatif)} – {formater_euros(prix_max_indicatif)}
            </div>
            <div class="prediction-detail">
                Estimation centrale : {formater_euros(prix_estime)}.
                {formater_euros(prix_m2)} / m² pour {formater_entier(surface)} m²,
                {formater_entier(nombre_pieces)} pièce(s), Paris {arrondissement}.
            </div>
            <div class="prediction-note">
                Cette fourchette correspond à l’estimation centrale, plus ou moins l’erreur
                moyenne observée du modèle ({formater_euros(mae_euros)}). Elle est indicative
                et ne constitue pas un intervalle de confiance.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    afficher_historique_predictions()

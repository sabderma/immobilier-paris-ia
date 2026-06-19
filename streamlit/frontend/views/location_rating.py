from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from frontend.api_client import (
    ErreurApi,
    api_delete,
    api_get_json,
    charger_commerces_paris,
    geocoder_adresse,
)
from frontend.config import API_ENDPOINTS
from frontend.formatting import formater_date, formater_decimal, formater_entier
from frontend.map_view import creer_carte_adresse


def supprimer_adresse_historique(address_id: int) -> None:
    try:
        api_delete(
            f"{API_ENDPOINTS['user_addresses']}/{address_id}",
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.error(exc.message)
        return

    st.success("Adresse supprimée de ton historique.")
    st.rerun()


def _formater_coordonnees(valeur: Any) -> str:
    try:
        return f"{float(valeur):.5f}"
    except (TypeError, ValueError):
        return "—"


def _carte_adresse_historique(ligne: dict[str, Any]) -> str:
    adresse = escape(str(ligne.get("address") or "Adresse exacte"))
    return f"""
        <article class="address-history-card">
            <div class="address-history-card-top">
                <span class="address-history-source">Adresse exacte</span>
                <span class="address-history-date">{formater_date(ligne.get("created_at"))}</span>
            </div>
            <div class="address-history-title">{adresse}</div>
            <div class="address-history-location">Adresse localisée avec les alentours</div>
            <div class="address-history-details">
                <span>
                    <strong>{_formater_coordonnees(ligne.get("latitude"))}</strong>
                    latitude
                </span>
                <span>
                    <strong>{_formater_coordonnees(ligne.get("longitude"))}</strong>
                    longitude
                </span>
            </div>
        </article>
    """


def afficher_historique_adresses() -> None:
    st.markdown("#### Historique de mes adresses exactes")

    try:
        historique = api_get_json(
            API_ENDPOINTS["user_addresses"],
            arreter_sur_erreur=False,
        )
    except ErreurApi as exc:
        st.caption(f"Historique indisponible : {exc.message}")
        return

    if not historique:
        st.info("Aucune adresse exacte enregistrée pour le moment.")
        return

    historique_trie = sorted(
        historique,
        key=lambda ligne: ligne.get("created_at") or "",
        reverse=True,
    )

    for ligne in historique_trie:
        address_id = int(ligne["id"])
        st.markdown(_carte_adresse_historique(ligne), unsafe_allow_html=True)
        if st.button(
            "Effacer",
            key=f"effacer_adresse_{address_id}",
            width="stretch",
        ):
            supprimer_adresse_historique(address_id)


def afficher_lieux_proches(
    lieux: list[dict[str, Any]],
    colonnes: list[str],
    libelles: dict[str, str],
) -> None:
    if not lieux:
        st.caption("Aucun résultat disponible dans ce rayon.")
        return

    tableau = pd.DataFrame(lieux[:30])
    for colonne in colonnes:
        if colonne not in tableau.columns:
            tableau[colonne] = ""
    tableau = tableau[colonnes].rename(columns=libelles)
    for colonne_liste in ("Modes", "Lignes"):
        if colonne_liste in tableau.columns:
            tableau[colonne_liste] = tableau[colonne_liste].apply(
                lambda valeur: ", ".join(valeur) if isinstance(valeur, list) else valeur
            )
    st.dataframe(tableau, hide_index=True, width="stretch")


def afficher_resultat_geocodage(resultat: dict[str, Any]) -> None:
    if resultat.get("erreur"):
        st.error(
            resultat.get(
                "message",
                "Il faut saisir une adresse exacte située à Paris.",
            )
        )
        return

    st.markdown("#### Adresse localisée par l’IGN")
    score = resultat.get("score_correspondance")
    score_affiche = f"{float(score) * 100:.1f} %" if score is not None else "—"

    col_adresse, col_score = st.columns([2, 1])
    with col_adresse:
        st.metric("Adresse normalisée", resultat.get("adresse_normalisee", "—"))
    with col_score:
        st.metric("Correspondance", score_affiche)

    latitude = float(resultat["latitude"])
    longitude = float(resultat["longitude"])
    adresse = str(resultat.get("adresse_normalisee") or "Adresse localisée")
    proximite = resultat.get("proximite") or {}
    totaux = proximite.get("totaux") or {}

    st.caption(
        f"Lieux recherchés dans un rayon de {proximite.get('rayon_metres', 500)} m "
        "à vol d’oiseau."
    )
    col_transport, col_commerce, col_ecole, col_sante = st.columns(4)
    with col_transport:
        st.metric("Transports", totaux.get("transports", 0))
    with col_commerce:
        st.metric("Commerces", totaux.get("commerces", 0))
    with col_ecole:
        st.metric("Écoles", totaux.get("education", 0))
    with col_sante:
        st.metric("Santé", totaux.get("sante", 0))

    carte = creer_carte_adresse(
        latitude=latitude,
        longitude=longitude,
        adresse=adresse,
        proximite=proximite,
    )
    st_folium(
        carte,
        key=f"carte_adresse_{resultat.get('identifiant_ban', 'ign')}",
        height=340,
        use_container_width=True,
        returned_objects=[],
    )

    resume_ia = resultat.get("resume_ia") or {}
    if resume_ia.get("texte"):
        with st.container(border=True):
            st.markdown("##### Résumé du secteur par OpenAI")
            st.write(resume_ia["texte"])
            st.caption(
                "Résumé généré à partir des données IGN, Île-de-France Mobilités "
                "et OpenStreetMap affichées sur cette page."
            )
    elif resume_ia.get("erreur"):
        st.caption("Le résumé OpenAI est temporairement indisponible.")

    erreurs = proximite.get("erreurs") or []
    for erreur in erreurs:
        st.warning(erreur)

    with st.expander("Transports proches"):
        afficher_lieux_proches(
            proximite.get("transports") or [],
            ["nom", "modes", "lignes", "distance_metres"],
            {
                "nom": "Arrêt ou station",
                "modes": "Modes",
                "lignes": "Lignes",
                "distance_metres": "Distance (m)",
            },
        )

    with st.expander("Commerces, écoles et santé proches"):
        afficher_lieux_proches(
            proximite.get("equipements") or [],
            ["nom", "categorie", "sous_categorie", "distance_metres"],
            {
                "nom": "Lieu",
                "categorie": "Catégorie",
                "sous_categorie": "Type",
                "distance_metres": "Distance (m)",
            },
        )

    st.caption(
        "Sources : Géoplateforme IGN, Île-de-France Mobilités, OpenStreetMap "
        "et résumé rédigé par OpenAI."
    )


def afficher_resultat_arrondissement(
    commerces: pd.DataFrame,
    arrondissement: int,
) -> None:
    selection = commerces[commerces["arrondissement"].astype(int) == arrondissement]
    if selection.empty:
        st.info("Aucune information disponible pour cet arrondissement.")
        return

    donnees = selection.iloc[0]
    st.markdown(f"#### {donnees['nom_arrondissement']}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Score arrondissement",
            formater_decimal(donnees.get("score_arrondissement_sur_10"), "/10"),
        )
    with col2:
        st.metric(
            "Proximité quotidienne",
            formater_decimal(
                donnees.get("score_proximite_quotidienne_sur_10"),
                "/10",
            ),
        )
    with col3:
        st.metric(
            "Diversité commerciale",
            formater_decimal(
                donnees.get("score_diversite_commerciale_sur_10"),
                "/10",
            ),
        )
    with col4:
        st.metric(
            "Grandes surfaces",
            formater_decimal(
                donnees.get("score_grandes_surfaces_sur_10"),
                "/10",
            ),
        )

    tableau = pd.DataFrame(
        [
            ("Population 2010", formater_entier(donnees.get("population_2010"))),
            ("Total commerces", formater_entier(donnees.get("total_commerces"))),
            (
                "Commerces / 10 000 hab.",
                formater_decimal(donnees.get("commerces_pour_10000_habitants")),
            ),
            ("Grandes surfaces", formater_entier(donnees.get("grandes_surfaces"))),
            (
                "Commerces alimentaires",
                formater_entier(donnees.get("commerces_alimentaires")),
            ),
            (
                "Commerces spécialisés",
                formater_entier(donnees.get("commerces_specialises")),
            ),
            ("Hypermarchés", formater_entier(donnees.get("hypermarche"))),
            ("Supermarchés", formater_entier(donnees.get("supermarche"))),
            ("Supérettes", formater_entier(donnees.get("superette"))),
            ("Épiceries", formater_entier(donnees.get("epicerie"))),
            ("Boulangeries", formater_entier(donnees.get("boulangerie"))),
            (
                "Boucheries-charcuteries",
                formater_entier(donnees.get("boucherie_charcuterie")),
            ),
            ("Poissonneries", formater_entier(donnees.get("poissonnerie"))),
            ("Fleuristes", formater_entier(donnees.get("fleuriste"))),
            ("Magasins d’optique", formater_entier(donnees.get("magasin_d_optique"))),
            ("Stations-service", formater_entier(donnees.get("station_service"))),
        ],
        columns=["Information", "Valeur"],
    )
    st.markdown(
        tableau.to_html(index=False, escape=True, classes="info-table"),
        unsafe_allow_html=True,
    )
    st.caption("Source : Open Data Île-de-France, Base permanente des équipements 2012.")


def afficher_noter_endroit() -> None:
    st.markdown("### Analyser votre endroit")

    commerces = charger_commerces_paris()
    if commerces.empty:
        st.info("Aucune donnée commerce disponible pour Paris.")
        return

    arrondissements = sorted(commerces["arrondissement"].astype(int).tolist())
    with st.container(border=True):
        st.markdown("#### Noter votre arrondissement")
        arrondissement = st.selectbox(
            "Choisir votre arrondissement",
            arrondissements,
            index=None,
            placeholder="",
            key="noter_arrondissement_select",
        )
        noter_arrondissement = st.button(
            "Noter cet arrondissement",
            type="primary",
            key="noter_arrondissement_bouton",
        )

    with st.container(border=True):
        st.markdown("#### Localiser votre adresse exacte avec les alentours")
        adresse_exacte = st.text_input(
            "Adresse exacte à Paris",
            placeholder="Ex : 71 rue de Passy, Paris 16e",
            key="noter_adresse_exacte",
        )
        st.caption(
            "Seules les adresses situées à Paris intra-muros sont acceptées."
        )
        localiser_adresse = st.button(
            "Localiser cette adresse",
            type="primary",
            key="geocoder_adresse_ign",
        )

    if localiser_adresse:
        if not adresse_exacte.strip():
            st.error("Renseigne une adresse complète à Paris.")
        else:
            with st.spinner("Recherche de l’adresse et des lieux proches..."):
                resultat_adresse = geocoder_adresse(adresse_exacte.strip())
            st.session_state["resultat_geocodage_adresse"] = resultat_adresse
            st.session_state.pop("arrondissement_note", None)

    if noter_arrondissement:
        if arrondissement is None:
            st.error("Choisis un arrondissement avant de lancer la notation.")
        else:
            st.session_state["arrondissement_note"] = arrondissement
            st.session_state.pop("resultat_geocodage_adresse", None)

    resultat_geocodage = st.session_state.get("resultat_geocodage_adresse")
    if resultat_geocodage:
        afficher_resultat_geocodage(resultat_geocodage)

    arrondissement_note = st.session_state.get("arrondissement_note")
    if arrondissement_note is not None and arrondissement_note == arrondissement:
        afficher_resultat_arrondissement(commerces, int(arrondissement_note))

    afficher_historique_adresses()

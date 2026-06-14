from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from frontend.api_client import charger_commerces_paris, noter_adresse_gemini
from frontend.formatting import formater_decimal, formater_entier


def libelle_categorie(categorie: str) -> str:
    libelles = {
        "transports": "Transports",
        "commerces": "Commerces",
        "ecoles": "Écoles",
        "espaces_verts": "Espaces verts",
        "sante": "Santé",
        "tourisme_frequentation": "Tourisme / fréquentation",
    }
    return libelles.get(categorie, categorie.replace("_", " ").title())


def lignes_resultat_adresse(resultat: dict[str, Any]) -> list[dict[str, str]]:
    lignes = []
    details = resultat.get("details", {})
    if not isinstance(details, dict):
        return lignes

    for categorie, donnees in details.items():
        if not isinstance(donnees, dict):
            continue

        elements = donnees.get("elements", [])
        if not isinstance(elements, list):
            continue

        for element in elements:
            if not isinstance(element, dict):
                continue

            lignes_transport = element.get("lignes", [])
            if isinstance(lignes_transport, list):
                lignes_transport = ", ".join(str(ligne) for ligne in lignes_transport)

            commentaire = element.get("commentaire") or element.get("impact") or ""
            lignes.append(
                {
                    "Catégorie": libelle_categorie(categorie),
                    "Nom": str(element.get("nom") or "Non renseigné"),
                    "Type": str(element.get("type") or "Non renseigné"),
                    "Lignes": str(lignes_transport or ""),
                    "Distance": str(
                        element.get("distance_estimee")
                        or "Distance approximative non renseignée"
                    ),
                    "Temps à pied": str(element.get("temps_a_pied") or ""),
                    "Avis": str(commentaire),
                }
            )

    return lignes


def afficher_resultat_adresse_gemini(resultat: dict[str, Any]) -> None:
    if resultat.get("erreur"):
        st.error(resultat.get("message", "Il faut saisir une adresse située à Paris."))
        return

    st.markdown("#### Résultat Gemini")
    score = resultat.get("score_global")
    niveau = resultat.get("niveau", "—")

    col_score, col_niveau = st.columns(2)
    with col_score:
        st.metric("Score emplacement", f"{score}/100" if score is not None else "—")
    with col_niveau:
        st.metric("Niveau", str(niveau).capitalize())

    resume = resultat.get("resume")
    if resume:
        st.markdown(str(resume))

    lignes = lignes_resultat_adresse(resultat)
    if lignes:
        tableau = pd.DataFrame(lignes)
        st.markdown(
            tableau.to_html(index=False, escape=True, classes="info-table"),
            unsafe_allow_html=True,
        )

    details = resultat.get("details", {})
    if isinstance(details, dict):
        tranquillite = details.get("tranquillite", {})
        if isinstance(tranquillite, dict) and tranquillite.get("avis"):
            st.markdown("#### Tranquillité")
            st.write(tranquillite["avis"])

        attractivite = details.get("attractivite_immobiliere", {})
        if isinstance(attractivite, dict) and attractivite.get("avis"):
            st.markdown("#### Attractivité immobilière")
            st.write(attractivite["avis"])

    points_forts = resultat.get("points_forts", [])
    points_faibles = resultat.get("points_faibles", [])
    if points_forts or points_faibles:
        st.markdown("#### Synthèse")
        max_lignes = max(len(points_forts), len(points_faibles))
        synthese = pd.DataFrame(
            {
                "Points forts": [
                    points_forts[index] if index < len(points_forts) else ""
                    for index in range(max_lignes)
                ],
                "Points faibles": [
                    points_faibles[index] if index < len(points_faibles) else ""
                    for index in range(max_lignes)
                ],
            }
        )
        st.markdown(
            synthese.to_html(index=False, escape=True, classes="info-table"),
            unsafe_allow_html=True,
        )

    conclusion = resultat.get("conclusion_acheteur")
    if conclusion:
        st.markdown("#### Conclusion acheteur")
        st.write(conclusion)


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
    st.caption(
        "La note compare la densité de commerces de cet arrondissement à celle "
        "des autres arrondissements parisiens."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Note commerces",
            formater_decimal(donnees.get("note_commerces_sur_10"), "/10"),
        )
    with col2:
        st.metric("Total commerces", formater_entier(donnees.get("total_commerces")))
    with col3:
        st.metric(
            "Commerces / 10 000 hab.",
            formater_decimal(donnees.get("commerces_pour_10000_habitants")),
        )

    tableau = pd.DataFrame(
        [
            ("Population 2010", formater_entier(donnees.get("population_2010"))),
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
    st.markdown("### Noter votre endroit")

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
        st.markdown("#### Noter votre adresse exacte")
        adresse_exacte = st.text_input(
            "Adresse exacte à Paris",
            placeholder="Ex : 71 rue de Passy, Paris 16e",
            key="noter_adresse_exacte",
        )
        st.caption(
            "Seules les adresses situées à Paris intra-muros sont acceptées."
        )
        analyser_adresse = st.button(
            "Noter cette adresse avec Gemini",
            type="primary",
            key="noter_adresse_gemini",
        )

    if analyser_adresse:
        if not adresse_exacte.strip():
            st.error("Renseigne une adresse complète à Paris.")
        else:
            with st.spinner("Gemini analyse l’adresse..."):
                resultat_adresse = noter_adresse_gemini(adresse_exacte.strip())
            afficher_resultat_adresse_gemini(resultat_adresse)

    if noter_arrondissement:
        if arrondissement is None:
            st.error("Choisis un arrondissement avant de lancer la notation.")
        else:
            st.session_state["arrondissement_note"] = arrondissement

    arrondissement_note = st.session_state.get("arrondissement_note")
    if arrondissement_note is not None and arrondissement_note == arrondissement:
        afficher_resultat_arrondissement(commerces, int(arrondissement_note))

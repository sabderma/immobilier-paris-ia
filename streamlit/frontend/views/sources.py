from __future__ import annotations

import streamlit as st


def afficher_sources_et_guide() -> None:
    st.markdown("### Guide utilisateur et sources des données")
    st.write(
        "Cette application aide à explorer les ventes d’appartements à Paris, "
        "estimer un prix et comparer l’environnement d’un arrondissement ou d’une adresse."
    )

    st.markdown("#### Comment utiliser l’application")
    st.markdown(
        """
        1. **Carte** : utilisez les filtres en haut de la page pour choisir un arrondissement,
           une période, une surface ou un nombre de pièces. La couleur indique le prix médian
           au m². En zoomant, les ventes apparaissent sous forme de points cliquables.
        2. **Appartements à vendre** : explorez les annonces issues du scraping, comparez
           les prix demandés et les ventes DVF 2025, puis filtrez par source ou caractéristiques.
        3. **Tableau** : consultez les ventes correspondant aux filtres et téléchargez-les
           au format CSV.
        4. **Prédire appartement** : renseignez la surface, le nombre de pièces et
           l’arrondissement pour obtenir une estimation basée sur les ventes DVF passées.
        5. **Noter votre endroit** : choisissez un arrondissement puis cliquez sur
           **Noter cet arrondissement** pour afficher sa densité commerciale. Pour une adresse
           précise, saisissez une adresse parisienne complète et lancez l’analyse Gemini.
        """
    )

    st.markdown("#### Comment sont calculés les résultats")
    st.markdown(
        """
        - Les prix, statistiques, graphiques et points de la carte reposent sur les ventes
          immobilières officielles DVF filtrées pour les appartements parisiens.
        - La prédiction de prix utilise un modèle XGBoost entraîné sur les données DVF
          2021 à 2025. C’est une estimation indicative, pas une expertise immobilière.
        - La note d’arrondissement mesure uniquement la densité de commerces pour
          10 000 habitants. L’arrondissement ayant la densité la plus élevée obtient 10/10,
          puis les autres sont notés proportionnellement.
        - La note d’une adresse exacte est générée par Gemini à partir de critères de proximité :
          transports, commerces, écoles, espaces verts, santé, fréquentation et tranquillité.
          Les informations et distances produites par l’IA peuvent être approximatives.
        """
    )

    st.markdown("#### Sources des données")
    st.markdown(
        """
        - **Ventes immobilières et entraînement du modèle** :
          [Demandes de valeurs foncières (DVF) sur data.gouv.fr](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres).
          Ces données publiques recensent les transactions immobilières enregistrées par
          l’administration fiscale.
        - **Annonces disponibles** : données collectées par scraping auprès de Century 21,
          Laforêt, Le Figaro Immobilier, Orpi et Stéphane Plaza, puis nettoyées dans la table
          PostgreSQL `golden_data_scraping`.
        - **Commerces par arrondissement** :
          [Base permanente des équipements 2012 sur Open Data Île-de-France](https://data.iledefrance.fr/explore/dataset/les-commerces-par-commune-ou-arrondissement-base-permanente-des-equipements/).
          L’application interroge directement l’API de ce jeu de données. Les populations
          utilisées pour calculer la densité datent de 2010.
        - **Sections cadastrales affichées sur la carte** :
          [Cadastre ouvert Etalab](https://cadastre.data.gouv.fr/datasets/plan-cadastral-informatise).
        - **Fond de carte** :
          [OpenStreetMap](https://www.openstreetmap.org/copyright).
        - **Analyse d’une adresse exacte** :
          [API Gemini de Google](https://ai.google.dev/gemini-api/docs).
          L’adresse saisie est envoyée à Gemini pour produire l’analyse.
        """
    )

    st.info(
        "Les résultats sont fournis à titre informatif. Les prix passés, la note commerciale "
        "et l’analyse par IA ne remplacent pas une visite du quartier ni l’avis d’un professionnel."
    )

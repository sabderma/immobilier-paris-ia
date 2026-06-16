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
        5. **Analyser votre endroit** : choisissez un arrondissement puis cliquez sur
           **Noter cet arrondissement** pour afficher sa densité commerciale. Pour une adresse
           précise, saisissez une adresse parisienne complète pour la localiser avec l’IGN et
           afficher les transports, commerces, écoles et services de santé dans un rayon de 500 m.
        """
    )

    st.markdown("#### Comment sont calculés les résultats")
    st.markdown(
        """
        - Les prix, statistiques, graphiques et points de la carte reposent sur les ventes
          immobilières officielles DVF filtrées pour les appartements parisiens.
        - La prédiction de prix utilise un modèle XGBoost entraîné sur les données DVF
          2021 à 2025. C’est une estimation indicative, pas une expertise immobilière.
        - Le score arrondissement mesure l’offre commerciale par habitant et compare les
          20 arrondissements. Il combine la proximité quotidienne (45 %), la diversité
          commerciale (35 %) et les grandes surfaces (20 %). Chaque critère utilise un
          barème progressif de 4 à 10 selon le classement relatif. Ce n’est pas une note
          globale sur la qualité de vie.
        - Le géocodage d’une adresse exacte vérifie qu’elle existe à Paris et retourne son adresse
          normalisée, ses coordonnées GPS et un score de correspondance.
        - L’analyse de proximité compte et localise les transports, commerces, écoles et services
          de santé présents dans un rayon de 500 m à vol d’oiseau autour de l’adresse.
        - OpenAI rédige ensuite un court résumé à partir de ces résultats. L’IA ne recherche
          pas les lieux et ne calcule pas les distances.
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
        - **Fond de carte** :
          [OpenStreetMap](https://www.openstreetmap.org/copyright).
        - **Géocodage d’une adresse exacte** :
          [Service de géocodage de la Géoplateforme IGN](https://geoservices.ign.fr/documentation/services/services-geoplateforme/geocodage).
          L’adresse saisie est comparée à la Base Adresse Nationale.
        - **Transports autour d’une adresse** :
          [API PRIM d’Île-de-France Mobilités](https://prim.iledefrance-mobilites.fr/fr/apis/idfm-navitia).
          Elle fournit les arrêts, stations, modes et lignes à proximité.
        - **Commerces, écoles et services de santé autour d’une adresse** :
          [OpenStreetMap](https://www.openstreetmap.org/copyright), interrogé avec l’API Overpass.
        - **Résumé du secteur** :
          [OpenAI](https://openai.com/), utilisé uniquement pour rédiger un texte à partir
          des données de proximité déjà collectées.
        """
    )

    st.info(
        "Les résultats sont fournis à titre informatif. Les prix passés, la note commerciale "
        "et les analyses de proximité ne remplaceront pas une visite du quartier "
        "ni l’avis d’un professionnel."
    )

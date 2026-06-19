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
        2. **Appartements à vendre** : explorez les annonces disponibles, comparez
           les prix demandés avec les ventes récentes, puis filtrez par source ou caractéristiques.
        3. **Tableau** : consultez les ventes correspondant aux filtres et téléchargez-les
           au format CSV.
        4. **Prédire appartement** : renseignez la surface, le nombre de pièces et
           l’arrondissement pour obtenir une estimation basée sur des ventes passées.
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
          immobilières officielles disponibles pour les appartements parisiens.
        - L’estimation de prix compare le bien saisi avec des ventes passées similaires.
          Elle reste indicative et ne remplace pas une expertise immobilière.
        - Le score arrondissement synthétise l’offre commerciale et la compare aux autres
          arrondissements parisiens. Ce n’est pas une note globale sur la qualité de vie.
        - L’adresse exacte est vérifiée avec les données de référence françaises, puis localisée
          pour afficher les transports, commerces, écoles et services de santé à proximité.
        - Le résumé du secteur est rédigé à partir des données affichées sur la page.
        """
    )

    st.markdown("#### Sources des données")
    st.markdown(
        """
        - **Ventes immobilières officielles** :
          [Demandes de valeurs foncières (DVF) sur data.gouv.fr](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres).
          Ces données publiques recensent les transactions immobilières enregistrées par
          l’administration fiscale.
        - **Annonces immobilières disponibles** : annonces publiées par Century 21,
          Laforêt, Le Figaro Immobilier, Orpi et Stéphane Plaza.
        - **Commerces par arrondissement** :
          [Base permanente des équipements 2012 sur Open Data Île-de-France](https://data.iledefrance.fr/explore/dataset/les-commerces-par-commune-ou-arrondissement-base-permanente-des-equipements/).
          Les populations utilisées pour calculer la densité datent de 2010.
        - **Fond de carte** :
          [OpenStreetMap](https://www.openstreetmap.org/copyright).
        - **Géocodage d’une adresse exacte** :
          [Service de géocodage de la Géoplateforme IGN](https://geoservices.ign.fr/documentation/services/services-geoplateforme/geocodage).
          L’adresse saisie est comparée à la Base Adresse Nationale.
        - **Transports autour d’une adresse** :
          [Île-de-France Mobilités](https://www.iledefrance-mobilites.fr/).
          Cette source fournit les arrêts, stations, modes et lignes à proximité.
        - **Commerces, écoles et services de santé autour d’une adresse** :
          [OpenStreetMap](https://www.openstreetmap.org/copyright).
        - **Résumé du secteur** :
          [OpenAI](https://openai.com/), utilisé pour rédiger un texte clair à partir
          des données de proximité affichées dans l’application.
        """
    )

    st.info(
        "Les résultats sont fournis à titre informatif. Les prix passés, la note commerciale "
        "et les analyses de proximité ne remplaceront pas une visite du quartier "
        "ni l’avis d’un professionnel."
    )

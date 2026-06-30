from __future__ import annotations

"""Service de proximite utilise par l'API de localisation en C17.

Il cherche les transports proches avec Ile-de-France Mobilites et les equipements
proches avec OpenStreetMap Overpass.
"""

import math
import os
from typing import Any

import requests
from fastapi import HTTPException, status

from api.core import charger_env


RAYON_PROXIMITE_METRES = 500
TIMEOUT_PROXIMITE_SECONDES = 35
IDFM_PLACES_NEARBY_URL = (
    "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/"
    "coverage/fr-idf/coords/{longitude};{latitude}/places_nearby"
)
IDFM_ARRETS_OPEN_DATA_URL = (
    "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/"
    "arrets-lignes/records"
)
OVERPASS_API_URLS = (
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
AMENITES_EDUCATION = {
    "school",
    "college",
    "university",
    "kindergarten",
    "childcare",
}
AMENITES_SANTE = {
    "doctors",
    "dentist",
    "pharmacy",
    "clinic",
    "hospital",
}


def distance_metres(
    latitude_depart: float,
    longitude_depart: float,
    latitude_arrivee: float,
    longitude_arrivee: float,
) -> int:
    """Calcule la distance à vol d'oiseau entre deux coordonnées GPS."""
    rayon_terre = 6_371_000
    lat1 = math.radians(latitude_depart)
    lat2 = math.radians(latitude_arrivee)
    delta_lat = math.radians(latitude_arrivee - latitude_depart)
    delta_lon = math.radians(longitude_arrivee - longitude_depart)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return round(rayon_terre * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def chercher_transports_idfm(
    latitude: float,
    longitude: float,
    rayon_metres: int = RAYON_PROXIMITE_METRES,
) -> list[dict[str, Any]]:
    """Cherche les arrets de transport autour d'une adresse."""
    # C17 : la cle IDFM reste dans l'environnement et pas dans le code.
    charger_env()
    api_key = os.getenv("IDFM_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le jeton IDFM_API_KEY n'est pas configuré.",
        )

    erreur_prim: Exception | None = None
    try:
        response = requests.get(
            IDFM_PLACES_NEARBY_URL.format(
                longitude=longitude,
                latitude=latitude,
            ),
            params={
                "distance": rayon_metres,
                "type[]": "stop_area",
                "count": 100,
                "depth": 3,
            },
            headers={"apikey": api_key},
            timeout=TIMEOUT_PROXIMITE_SECONDES,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        erreur_prim = exc
        # Si PRIM ne repond pas, on essaye la source open data IDFM.
        return chercher_transports_idfm_open_data(
            latitude,
            longitude,
            rayon_metres,
            erreur_prim,
        )

    transports = []
    for lieu in payload.get("places_nearby", []):
        arret = lieu.get("stop_area") or {}
        coordonnees = arret.get("coord") or {}
        if not coordonnees.get("lat") or not coordonnees.get("lon"):
            continue

        modes = sorted(
            {
                str(mode.get("name"))
                for mode in arret.get("commercial_modes", [])
                if mode.get("name")
            }
        )
        lignes = sorted(
            {
                str(ligne.get("code") or ligne.get("name"))
                for ligne in arret.get("lines", [])
                if ligne.get("code") or ligne.get("name")
            }
        )
        transports.append(
            {
                "id": arret.get("id") or lieu.get("id"),
                "nom": arret.get("name") or lieu.get("name") or "Arrêt sans nom",
                "categorie": "transport",
                "sous_categorie": ", ".join(modes) or "Transport",
                "modes": modes,
                "lignes": lignes,
                "latitude": float(coordonnees["lat"]),
                "longitude": float(coordonnees["lon"]),
                "distance_metres": int(lieu.get("distance") or 0),
                "source": "Île-de-France Mobilités",
            }
        )

    return sorted(transports, key=lambda lieu: lieu["distance_metres"])


def chercher_transports_idfm_open_data(
    latitude: float,
    longitude: float,
    rayon_metres: int,
    erreur_prim: Exception | None = None,
) -> list[dict[str, Any]]:
    """Utilise le référentiel officiel IDFM si l'API PRIM est inaccessible."""
    # C17 : cette source sert de secours si l'API principale IDFM ne repond pas.
    try:
        response = requests.get(
            IDFM_ARRETS_OPEN_DATA_URL,
            params={
                "where": (
                    "distance(pointgeo, "
                    f"geom'POINT({longitude} {latitude})', {rayon_metres}m)"
                ),
                "select": (
                    "stop_id,stop_name,stop_lon,stop_lat,mode,shortname,pointgeo"
                ),
                "limit": 100,
            },
            timeout=TIMEOUT_PROXIMITE_SECONDES,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de transports Île-de-France Mobilités est indisponible.",
        ) from (erreur_prim or exc)

    arrets: dict[str, dict[str, Any]] = {}
    for ligne in payload.get("results", []):
        point = ligne.get("pointgeo") or {}
        latitude_arret = point.get("lat") or ligne.get("stop_lat")
        longitude_arret = point.get("lon") or ligne.get("stop_lon")
        if latitude_arret is None or longitude_arret is None:
            continue

        identifiant = str(
            ligne.get("stop_id")
            or f"{ligne.get('stop_name')}:{latitude_arret}:{longitude_arret}"
        )
        arret = arrets.setdefault(
            identifiant,
            {
                "id": identifiant,
                "nom": ligne.get("stop_name") or "Arrêt sans nom",
                "categorie": "transport",
                "modes": set(),
                "lignes": set(),
                "latitude": float(latitude_arret),
                "longitude": float(longitude_arret),
                "source": "Île-de-France Mobilités - Open Data",
            },
        )
        if ligne.get("mode"):
            arret["modes"].add(str(ligne["mode"]))
        if ligne.get("shortname"):
            arret["lignes"].add(str(ligne["shortname"]))

    transports = []
    for arret in arrets.values():
        arret["modes"] = sorted(arret["modes"])
        arret["lignes"] = sorted(arret["lignes"])
        arret["sous_categorie"] = ", ".join(arret["modes"]) or "Transport"
        arret["distance_metres"] = distance_metres(
            latitude,
            longitude,
            arret["latitude"],
            arret["longitude"],
        )
        transports.append(arret)

    return sorted(transports, key=lambda lieu: lieu["distance_metres"])


def construire_requete_overpass(
    latitude: float,
    longitude: float,
    rayon_metres: int,
) -> str:
    """Construit la requete envoyee a OpenStreetMap Overpass."""
    return f"""
[out:json][timeout:25];
(
  nwr["shop"](around:{rayon_metres},{latitude},{longitude});
  nwr["amenity"~"^(school|college|university|kindergarten|childcare)$"](around:{rayon_metres},{latitude},{longitude});
  nwr["amenity"~"^(doctors|dentist|pharmacy|clinic|hospital)$"](around:{rayon_metres},{latitude},{longitude});
);
out center tags;
""".strip()


def categorie_equipement(tags: dict[str, Any]) -> tuple[str, str] | None:
    """Classe un lieu OpenStreetMap en commerce, education ou sante."""
    type_commerce = tags.get("shop")
    if type_commerce and type_commerce != "vacant":
        return "commerce", str(type_commerce)

    amenity = tags.get("amenity")
    if amenity in AMENITES_EDUCATION:
        return "education", str(tags.get("school:FR") or amenity)
    if amenity in AMENITES_SANTE:
        return "sante", str(amenity)
    return None


def normaliser_equipement_overpass(
    element: dict[str, Any],
    latitude_adresse: float,
    longitude_adresse: float,
) -> dict[str, Any] | None:
    """Transforme un lieu Overpass en objet JSON simple pour l'API."""
    tags = element.get("tags") or {}
    categorie = categorie_equipement(tags)
    if categorie is None:
        return None

    centre = element.get("center") or element
    latitude = centre.get("lat")
    longitude = centre.get("lon")
    if latitude is None or longitude is None:
        return None

    nom = tags.get("name") or tags.get("brand") or tags.get("operator")
    if not nom:
        return None

    categorie_nom, sous_categorie = categorie
    return {
        "id": f"osm:{element.get('type')}:{element.get('id')}",
        "nom": str(nom),
        "categorie": categorie_nom,
        "sous_categorie": sous_categorie,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "distance_metres": distance_metres(
            latitude_adresse,
            longitude_adresse,
            float(latitude),
            float(longitude),
        ),
        "source": "OpenStreetMap",
    }


def chercher_equipements_overpass(
    latitude: float,
    longitude: float,
    rayon_metres: int = RAYON_PROXIMITE_METRES,
) -> list[dict[str, Any]]:
    """Cherche les commerces, ecoles et lieux de sante autour d'un point."""
    requete = construire_requete_overpass(latitude, longitude, rayon_metres)
    derniere_erreur: Exception | None = None

    for api_url in OVERPASS_API_URLS:
        # C17 : plusieurs URLs Overpass sont essayees pour eviter un blocage simple.
        try:
            response = requests.post(
                api_url,
                data={"data": requete},
                headers={"User-Agent": "immobilier-paris-ia/1.0"},
                timeout=TIMEOUT_PROXIMITE_SECONDES,
            )
            response.raise_for_status()
            payload = response.json()
            break
        except (requests.RequestException, ValueError) as exc:
            derniere_erreur = exc
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service OpenStreetMap Overpass est indisponible.",
        ) from derniere_erreur

    equipements = []
    identifiants = set()
    for element in payload.get("elements", []):
        equipement = normaliser_equipement_overpass(element, latitude, longitude)
        if equipement is None or equipement["id"] in identifiants:
            continue
        identifiants.add(equipement["id"])
        equipements.append(equipement)

    return sorted(equipements, key=lambda lieu: lieu["distance_metres"])


def analyser_proximite(
    latitude: float,
    longitude: float,
    rayon_metres: int = RAYON_PROXIMITE_METRES,
) -> dict[str, Any]:
    """Regroupe les transports et equipements proches dans une seule reponse."""
    # C17 : la reponse est deja organisee pour etre affichee directement par Streamlit.
    resultat: dict[str, Any] = {
        "rayon_metres": rayon_metres,
        "distance": "à vol d'oiseau",
        "transports": [],
        "equipements": [],
        "erreurs": [],
    }

    try:
        resultat["transports"] = chercher_transports_idfm(
            latitude,
            longitude,
            rayon_metres,
        )
    except HTTPException as exc:
        # On garde l'erreur mais on continue avec les autres sources possibles.
        resultat["erreurs"].append(str(exc.detail))

    try:
        resultat["equipements"] = chercher_equipements_overpass(
            latitude,
            longitude,
            rayon_metres,
        )
    except HTTPException as exc:
        resultat["erreurs"].append(str(exc.detail))

    resultat["totaux"] = {
        "transports": len(resultat["transports"]),
        "commerces": sum(
            lieu["categorie"] == "commerce" for lieu in resultat["equipements"]
        ),
        "education": sum(
            lieu["categorie"] == "education" for lieu in resultat["equipements"]
        ),
        "sante": sum(lieu["categorie"] == "sante" for lieu in resultat["equipements"]),
    }
    return resultat

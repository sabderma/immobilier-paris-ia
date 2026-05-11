import pandas as pd
import re
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "processed" / "annonces_scraping_fusionnees.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "annonces_scraping_nettoyees_master.csv"

# =====================================================
# VALEURS CONSIDÉRÉES COMME MANQUANTES
# =====================================================

VALEURS_MANQUANTES = [
    "",
    "non disponible",
    "n/a",
    "na",
    "null",
    "none",
    "nan",
    "non renseigné",
    "non renseigne"
]


def est_valeur_manquante(val):
    """Vérifie si une valeur est vide ou non disponible."""
    if pd.isna(val):
        return True

    val = str(val).lower().strip()

    return val in VALEURS_MANQUANTES


# =====================================================
# FONCTIONS DE NETTOYAGE
# =====================================================

def clean_prix(val):
    """Nettoie le prix : '550 000 €' -> 550000.0"""
    if est_valeur_manquante(val):
        return val

    s = str(val).lower().strip().replace("\xa0", " ")

    if "€" in s:
        s = s.split("€")[0]

    s = s.replace(" ", "").replace(",", ".")

    digits = "".join(c for c in s if c.isdigit() or c == ".")

    return float(digits) if digits else None


def clean_surface(val):
    """Nettoie la surface : '54 m²' -> 54.0"""
    if est_valeur_manquante(val):
        return val

    s = str(val).lower().strip().replace("\xa0", " ")

    s = s.replace("m²", "")
    s = s.replace("m2", "")
    s = s.replace("m", "")
    s = s.replace(" ", "")
    s = s.replace(",", ".")

    digits = "".join(c for c in s if c.isdigit() or c == ".")

    return float(digits) if digits else None


def clean_prix_m2(val):
    """Nettoie le prix au m² : '10 185 €/m²' -> 10185.0"""
    if est_valeur_manquante(val):
        return val

    s = str(val).lower().strip().replace("\xa0", " ")

    mots_a_supprimer = [
        "soit",
        "€/m²",
        "€/m2",
        "/m²",
        "/m2",
        "/ m²",
        "/ m2",
        "€"
    ]

    for mot in mots_a_supprimer:
        s = s.replace(mot, "")

    s = s.replace(" ", "")
    s = s.replace(",", ".")

    digits = "".join(c for c in s if c.isdigit() or c == ".")

    return float(digits) if digits else None


def clean_type(val_type, val_details):
    """
    Nettoie le type de bien.

    Exemple :
    'Appartement F3 à vendre' -> 'Appartement'
    'Maison neuve à vendre' -> 'Maison'
    'Locaux professionnels' -> 'Locaux'
    """

    t = "" if pd.isna(val_type) else str(val_type).lower().strip()
    d = "" if pd.isna(val_details) else str(val_details).lower().strip()

    texte = t + " " + d

    if "appartement" in texte or "appart" in texte:
        return "Appartement"

    if "studio" in texte:
        return "Appartement"

    if "duplex" in texte:
        return "Appartement"

    if "loft" in texte:
        return "Appartement"

    if "maison" in texte or "villa" in texte:
        return "Maison"

    if "local" in texte or "locaux" in texte:
        return "Locaux"

    if est_valeur_manquante(t):
        return None

    if " à " in t:
        t = t.split(" à ")[0].strip()

    if " a " in t:
        t = t.split(" a ")[0].strip()

    return t.capitalize() if t else None


def clean_nb_pieces(val):
    """Nettoie le nombre de pièces : '3 pièces' -> 3."""
    if est_valeur_manquante(val):
        return val

    s = str(val).lower()

    if "studio" in s:
        return 1

    m = re.search(r"\d+", s)

    return int(m.group()) if m else None


def clean_localisation(val):
    """
    Nettoie la localisation.

    Exemple :
    'PARIS 75018' -> '75018'
    'Paris 75006' -> '75006'
    """

    if est_valeur_manquante(val):
        return val

    s = str(val).lower().strip()

    m = re.search(r"\b75\d{3}\b", s)

    if m:
        return m.group()

    s = s.replace("paris", "").strip()

    return s.capitalize() if s else None


# =====================================================
# FONCTIONS PRINCIPALES
# =====================================================

def charger_donnees():
    """Charge le fichier CSV brut."""
    print("Chargement du fichier CSV...")

    df = pd.read_csv(INPUT_PATH)

    print("Fichier chargé.")
    print("Nombre de lignes brutes :", len(df))
    print("Colonnes :", list(df.columns))

    return df


def verifier_colonnes(df):
    """Vérifie que toutes les colonnes nécessaires existent."""

    colonnes_obligatoires = [
        "type",
        "prix",
        "surface",
        "nb_pieces",
        "localisation",
        "details",
        "source",
        "prix_m2"
    ]

    colonnes_manquantes = []

    for colonne in colonnes_obligatoires:
        if colonne not in df.columns:
            colonnes_manquantes.append(colonne)

    if colonnes_manquantes:
        raise ValueError(f"Colonnes manquantes dans le CSV : {colonnes_manquantes}")


def nettoyer_donnees(df):
    """Applique tout le nettoyage sur le DataFrame."""

    print("\nDébut du nettoyage...")

    df = df.copy()
    # Uniformisation des valeurs manquantes dans toutes les colonnes
    df = df.replace([
        "non renseigne",
        "non renseigné",
        "n/a",
        "na",
        "null",
        "none",
        ""
    ], "non disponible")

    # Nettoyage du type
    print("Nettoyage de la colonne type...")
    df["type_clean"] = df.apply(
        lambda row: clean_type(row["type"], row["details"]),
        axis=1
    )

    # Suppression des types non utiles
    print("Suppression des types non utiles...")

    type_lower = df["type_clean"].fillna("").str.lower()

    types_a_supprimer = (
        type_lower.str.contains("péniche")
        | type_lower.str.contains("peniche")
        | type_lower.str.contains("viager")
        | type_lower.str.contains("hôtel")
        | type_lower.str.contains("hotel")
        | type_lower.str.contains("immeuble")
        | type_lower.str.contains("propriété")
        | type_lower.str.contains("propriete")
    )

    print("Lignes supprimées type non utile :", types_a_supprimer.sum())

    df = df[~types_a_supprimer]

    # Nettoyage numérique
    print("Nettoyage des colonnes numériques...")

    df["prix_clean"] = df["prix"].apply(clean_prix)
    df["surface_clean"] = df["surface"].apply(clean_surface)
    df["prix_m2_clean"] = df["prix_m2"].apply(clean_prix_m2)
    df["nb_pieces_clean"] = df["nb_pieces"].apply(clean_nb_pieces)

    # Nettoyage localisation
    print("Nettoyage de la localisation...")

    df["localisation_clean"] = df["localisation"].apply(clean_localisation)

    # Calcul prix/m² si absent
    print("Calcul du prix/m² manquant...")

    mask_prix_m2_manquant = (
        pd.to_numeric(df["prix_m2_clean"], errors="coerce").isna()
        & pd.to_numeric(df["prix_clean"], errors="coerce").notna()
        & pd.to_numeric(df["surface_clean"], errors="coerce").notna()
        & (pd.to_numeric(df["surface_clean"], errors="coerce") > 0)
    )

    df.loc[mask_prix_m2_manquant, "prix_m2_clean"] = (
        pd.to_numeric(df.loc[mask_prix_m2_manquant, "prix_clean"], errors="coerce")
        / pd.to_numeric(df.loc[mask_prix_m2_manquant, "surface_clean"], errors="coerce")
    )

    df["prix_m2_clean"] = df["prix_m2_clean"].apply(
    lambda x: round(x, 2) if isinstance(x, (int, float)) else x
     ) 
    
    

    # Création du DataFrame final
    df_clean = df[[
        "source",
        "type_clean",
        "prix_clean",
        "surface_clean",
        "prix_m2_clean",
        "nb_pieces_clean",
        "localisation_clean",
        "details"
    ]].rename(columns={
        "type_clean": "type",
        "prix_clean": "prix",
        "surface_clean": "surface",
        "prix_m2_clean": "prix_m2",
        "nb_pieces_clean": "nb_pieces",
        "localisation_clean": "localisation"
    })

    # Suppression des doublons
    doublons = df_clean.duplicated().sum()
    print("Doublons supprimés :", doublons)

    df_clean = df_clean.drop_duplicates()

    return df_clean



def exporter_donnees(df_clean):
    """Exporte le fichier nettoyé."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df_clean.to_csv(
        OUTPUT_PATH,
        sep=";",
        index=False,
        encoding="utf-8"
    )

    print("\nNettoyage terminé.")
    print("Fichier généré :", OUTPUT_PATH)
    print("Nombre de lignes finales :", len(df_clean))


def main():
    """Fonction principale."""

    df = charger_donnees()

    verifier_colonnes(df)

    df_clean = nettoyer_donnees(df)

    exporter_donnees(df_clean)


if __name__ == "__main__":
    main()
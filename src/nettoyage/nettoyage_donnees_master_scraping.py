import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "processed" / "annonces_scraping_nettoyees_master.csv"
OUTPUT_PATH = BASE_DIR / "data" / "final" / "annonces_scraping_nettoyees_golden.csv"


def est_non_disponible(val):
    return str(val).strip().lower() == "non disponible"


def nettoyer_details(val):
    if est_non_disponible(val):
        return ""

    return str(val).strip()


def extraire_prix(details):
    s = str(details).lower().replace("\xa0", " ")
    m = re.search(r"(\d[\d\s]{2,})\s*€", s)

    if m:
        return m.group(1).replace(" ", "")

    return "non disponible"


def extraire_surface(details):
    s = str(details).lower().replace("\xa0", " ")
    m = re.search(r"(\d+(?:[,.]\d+)?)\s*(m²|m2)", s)

    if m:
        return m.group(1).replace(",", ".")

    return "non disponible"


def extraire_nb_pieces(details):
    s = str(details).lower()

    if "studio" in s:
        return "1"

    m = re.search(r"(\d+)\s*pi[eè]ces?", s)

    if m:
        return m.group(1)

    return "non disponible"


def extraire_prix_m2(details):
    s = str(details).lower().replace("\xa0", " ")
    m = re.search(r"(\d[\d\s]*)\s*€\s*/\s*m[²2]", s)

    if m:
        return m.group(1).replace(" ", "")

    return "non disponible"


def extraire_code_paris(val):
    if pd.isna(val):
        return None

    s = str(val).strip().lower()

    if s == "" or s == "non disponible":
        return None

    m_code = re.search(r"\b75\d{3}\b", s)

    if m_code:
        code = m_code.group()

        if re.match(r"^750(0[1-9]|1[0-9]|20)$", code):
            return code

        return None

    m_arr = re.match(r"^\s*(\d{1,2})(er|ème|eme|e)?\b", s)

    if m_arr:
        arr = int(m_arr.group(1))

        if 1 <= arr <= 20:
            return f"75{arr:03d}"

    return None


if not INPUT_PATH.is_file():
    print("Fichier introuvable :", INPUT_PATH)
    raise SystemExit(1)

df = pd.read_csv(INPUT_PATH, sep=";", dtype=str)

print("Fichier chargé.")
print("Nombre de lignes au départ :", len(df))
print("Colonnes :", list(df.columns))
print()


colonnes_obligatoires = [
    "prix",
    "surface",
    "nb_pieces",
    "prix_m2",
    "details",
    "localisation"
]

for colonne in colonnes_obligatoires:
    if colonne not in df.columns:
        print(f"Colonne absente : {colonne}")
        raise SystemExit(1)


df = df.fillna("non disponible")
df = df.replace("", "non disponible")

df["details"] = df["details"].apply(nettoyer_details)


# ================================
# 1) NLP depuis details
# ================================

avant_prix = df["prix"].apply(est_non_disponible).sum()
avant_surface = df["surface"].apply(est_non_disponible).sum()
avant_nb_pieces = df["nb_pieces"].apply(est_non_disponible).sum()
avant_prix_m2 = df["prix_m2"].apply(est_non_disponible).sum()

print("Valeurs non disponibles avant NLP :")
print("prix :", avant_prix)
print("surface :", avant_surface)
print("nb_pieces :", avant_nb_pieces)
print("prix_m2 :", avant_prix_m2)
print()

mask_prix = df["prix"].apply(est_non_disponible)
df.loc[mask_prix, "prix"] = df.loc[mask_prix, "details"].apply(extraire_prix)

mask_surface = df["surface"].apply(est_non_disponible)
df.loc[mask_surface, "surface"] = df.loc[mask_surface, "details"].apply(extraire_surface)

mask_nb_pieces = df["nb_pieces"].apply(est_non_disponible)
df.loc[mask_nb_pieces, "nb_pieces"] = df.loc[mask_nb_pieces, "details"].apply(extraire_nb_pieces)

mask_prix_m2 = df["prix_m2"].apply(est_non_disponible)
df.loc[mask_prix_m2, "prix_m2"] = df.loc[mask_prix_m2, "details"].apply(extraire_prix_m2)

apres_prix = df["prix"].apply(est_non_disponible).sum()
apres_surface = df["surface"].apply(est_non_disponible).sum()
apres_nb_pieces = df["nb_pieces"].apply(est_non_disponible).sum()
apres_prix_m2 = df["prix_m2"].apply(est_non_disponible).sum()

print("Valeurs remplies par NLP :")
print("prix :", avant_prix - apres_prix)
print("surface :", avant_surface - apres_surface)
print("nb_pieces :", avant_nb_pieces - apres_nb_pieces)
print("prix_m2 :", avant_prix_m2 - apres_prix_m2)
print()


# ================================
# 2) Géolocalisation Paris
# ================================

print("Nettoyage de la localisation...")

df["loc_code"] = df["localisation"].apply(extraire_code_paris)

print("Répartition des codes postaux :")
print(df["loc_code"].value_counts().sort_index())
print()

avant_geo = len(df)

df = df[df["loc_code"].notna()].copy()
df["localisation"] = df["loc_code"]
df = df.drop(columns=["loc_code"])

print("Lignes supprimées hors Paris :", avant_geo - len(df))
print("Lignes conservées Paris 75001 à 75020 :", len(df))
print()


# ================================
# 3) Suppression des lignes incomplètes
# ================================

colonnes_a_verifier = ["prix", "surface", "nb_pieces", "prix_m2"]

avant_suppression = len(df)

df = df[
    ~df[colonnes_a_verifier]
    .apply(
        lambda row: row.astype(str)
        .str.lower()
        .str.strip()
        .eq("non disponible")
        .any(),
        axis=1
    )
].copy()

lignes_supprimees = avant_suppression - len(df)

print("Lignes supprimées car encore incomplètes :", lignes_supprimees)
print("Nombre de lignes finales :", len(df))

if "details" in df.columns:
    df = df.drop(columns=["details"])

# ================================
# 4) Export
# ================================

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(
    OUTPUT_PATH,
    sep=";",
    index=False,
    encoding="utf-8"
)

print("Fichier généré :", OUTPUT_PATH)
print("Terminé.")
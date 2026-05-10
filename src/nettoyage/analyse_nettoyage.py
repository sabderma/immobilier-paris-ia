import pandas as pd


# CHARGEMENT DU FICHIER
df = pd.read_csv("data/processed/annonces_scraping_fusionnees.csv")


# INFORMATIONS GÉNÉRALES
print("\n========== INFORMATIONS GÉNÉRALES ==========\n")

print("Nombre de lignes :", df.shape[0])
print("Nombre de colonnes :", df.shape[1])

print("\nColonnes du fichier :")
print(df.columns.tolist())


# TYPES DES COLONNES
print("\n========== TYPES DES COLONNES ==========\n")
print(df.dtypes)


# VALEURS MANQUANTES
print("\n========== VALEURS MANQUANTES ==========\n")

print(df.isnull().sum())

# VALEURS 'NON DISPONIBLE'
print("\n========== VALEURS 'NON DISPONIBLE' ==========\n")

for colonne in df.columns:
    
    nb_non_disponible = (
        df[colonne]
        .astype(str)
        .str.lower()
        .str.strip()
        .isin([
            "non disponible",
            "non renseigne",
            "non renseigné",
            "n/a",
            "na",
            "null",
            "none",
            ""
        ])
        .sum()
    )

    print(f"{colonne} : {nb_non_disponible}")


# TOTAL VALEURS VIDES + NON DISPONIBLE
print("\n========== TOTAL VALEURS PROBLÉMATIQUES ==========\n")

for colonne in df.columns:

    valeurs_vides = df[colonne].isnull().sum()

    non_disponible = (
        df[colonne]
        .astype(str)
        .str.lower()
        .str.strip()
        .isin([
            "non disponible",
            "non renseigne",
            "non renseigné",
            "n/a",
            "na",
            "null",
            "none",
            ""
        ])
        .sum()
    )

    total = valeurs_vides + non_disponible

    print(f"{colonne} : {total}")


# DOUBLONS
print("\n========== DOUBLONS ==========\n")

print("Nombre de lignes dupliquées :", df.duplicated().sum())


# APERÇU DES DONNÉES
print("\n========== APERÇU DES DONNÉES ==========\n")

print(df.head())


# STATISTIQUES
print("\n========== STATISTIQUES ==========\n")

print(df.describe(include="all"))


# STRUCTURE COMPLÈTE
print("\n========== STRUCTURE DATAFRAME ==========\n")

df.info()
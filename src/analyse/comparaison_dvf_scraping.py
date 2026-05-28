from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os

# ================================
# CONFIGURATION POSTGRESQL
# ================================

ROOT_DIR = Path(__file__).resolve().parents[2]


def charger_env() -> None:
    """Charge les variables du fichier .env local si elles existent."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for ligne in env_path.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue

        cle, valeur = ligne.split("=", 1)
        os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))


def construire_engine():
    charger_env()

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "immobilier_paris"),
    )
    return create_engine(url)


engine = construire_engine()

# ================================
# DOSSIER DE SORTIE
# ================================

OUTPUT_DIR = "data/visuals/comparaison_dvf_scrap"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def formater_effectif(valeur):
    return f"{int(valeur):,}".replace(",", " ")


def annoter_effectifs(ax, barres, effectifs):
    decalage = ax.get_ylim()[1] * 0.015

    for barre, effectif in zip(barres, effectifs):
        hauteur = barre.get_height()

        ax.text(
            barre.get_x() + barre.get_width() / 2,
            hauteur + decalage,
            f"n={formater_effectif(effectif)}",
            ha="center",
            va="bottom",
            fontsize=7,
            rotation=90
        )


def creer_tableau_visuel(df_tableau, chemin_sortie, titre):
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")

    tableau = ax.table(
        cellText=df_tableau.values,
        colLabels=df_tableau.columns,
        cellLoc="center",
        loc="center"
    )

    tableau.auto_set_font_size(False)
    tableau.set_fontsize(9)
    tableau.scale(1, 1.5)

    for (ligne, colonne), cellule in tableau.get_celld().items():
        if ligne == 0:
            cellule.set_text_props(weight="bold", color="white")
            cellule.set_facecolor("#1f4e79")
        elif ligne % 2 == 0:
            cellule.set_facecolor("#f2f2f2")

    ax.set_title(titre, fontsize=14, fontweight="bold", pad=18)
    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=300, bbox_inches="tight")
    plt.close()

# ================================
# 1. PRIX MOYEN AU M² PAR ARRONDISSEMENT
# ================================

query_arrondissement = """
WITH scraping_clean AS (
    SELECT
        CAST(SUBSTRING(localisation FROM '750([0-9]{2})') AS INTEGER) AS arrondissement,
        prix_m2
    FROM golden_data_scraping
    WHERE prix_m2 IS NOT NULL
      AND localisation IS NOT NULL
      AND localisation LIKE '%750%'
),
dvf_moyenne AS (
    SELECT
        arrondissement,
        AVG(prix_m2) AS prix_m2_dvf,
        COUNT(*) AS nb_observations_dvf
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND arrondissement IS NOT NULL
      AND annee_vente = 2025
    GROUP BY arrondissement
),
scraping_moyenne AS (
    SELECT
        arrondissement,
        AVG(prix_m2) AS prix_m2_scraping,
        COUNT(*) AS nb_observations_scraping
    FROM scraping_clean
    WHERE arrondissement IS NOT NULL
    GROUP BY arrondissement
)
SELECT
    d.arrondissement,
    d.prix_m2_dvf,
    s.prix_m2_scraping,
    d.nb_observations_dvf,
    s.nb_observations_scraping
FROM dvf_moyenne d
JOIN scraping_moyenne s
ON d.arrondissement = s.arrondissement
ORDER BY d.arrondissement;
"""

with engine.connect() as conn:
    df_arr = pd.read_sql(text(query_arrondissement), conn)

# ================================
# GRAPHIQUE 1
# ================================

fig, ax = plt.subplots(figsize=(14, 7))

x = range(len(df_arr))
width = 0.4

barres_dvf = ax.bar(
    [i - width / 2 for i in x],
    df_arr["prix_m2_dvf"],
    width=width,
    label="DVF 2025 - prix réel vendu"
)

barres_scraping = ax.bar(
    [i + width / 2 for i in x],
    df_arr["prix_m2_scraping"],
    width=width,
    label="Scraping - prix affiché"
)

ax.set_ylim(top=max(df_arr["prix_m2_dvf"].max(), df_arr["prix_m2_scraping"].max()) * 1.2)
annoter_effectifs(ax, barres_dvf, df_arr["nb_observations_dvf"])
annoter_effectifs(ax, barres_scraping, df_arr["nb_observations_scraping"])

ax.set_title("Comparaison du prix moyen au m² par arrondissement (DVF 2025)", fontsize=16)
ax.set_xlabel("Arrondissement")
ax.set_ylabel("Prix moyen au m² (€)")
ax.set_xticks(list(x))
ax.set_xticklabels(df_arr["arrondissement"])
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/comparaison_prix_m2_arrondissement.png", dpi=300)
plt.show()

# ================================
# 2. ÉCART ENTRE PRIX ANNONCÉ ET PRIX RÉEL
# ================================

df_arr["ecart_euros"] = df_arr["prix_m2_scraping"] - df_arr["prix_m2_dvf"]
df_arr["ecart_pourcentage"] = (
    df_arr["ecart_euros"] / df_arr["prix_m2_dvf"]
) * 100

df_ecart = df_arr.sort_values("ecart_pourcentage", ascending=False)

top_5_ecarts = df_ecart[
    [
        "arrondissement",
        "prix_m2_dvf",
        "prix_m2_scraping",
        "ecart_euros",
        "ecart_pourcentage",
        "nb_observations_dvf",
        "nb_observations_scraping"
    ]
].head(5).copy()

top_5_ecarts["arrondissement"] = top_5_ecarts["arrondissement"].astype(int)
top_5_ecarts["prix_m2_dvf"] = top_5_ecarts["prix_m2_dvf"].map(
    lambda x: f"{x:,.0f} €".replace(",", " ")
)
top_5_ecarts["prix_m2_scraping"] = top_5_ecarts["prix_m2_scraping"].map(
    lambda x: f"{x:,.0f} €".replace(",", " ")
)
top_5_ecarts["ecart_euros"] = top_5_ecarts["ecart_euros"].map(
    lambda x: f"{x:,.0f} €".replace(",", " ")
)
top_5_ecarts["ecart_pourcentage"] = top_5_ecarts["ecart_pourcentage"].map(
    lambda x: f"{x:.1f} %"
)
top_5_ecarts["nb_observations_dvf"] = top_5_ecarts["nb_observations_dvf"].map(
    formater_effectif
)
top_5_ecarts["nb_observations_scraping"] = top_5_ecarts["nb_observations_scraping"].map(
    formater_effectif
)

top_5_ecarts = top_5_ecarts.rename(columns={
    "arrondissement": "Arr.",
    "prix_m2_dvf": "DVF 2025",
    "prix_m2_scraping": "Annonces",
    "ecart_euros": "Écart €",
    "ecart_pourcentage": "Écart %",
    "nb_observations_dvf": "n DVF",
    "nb_observations_scraping": "n annonces"
})

creer_tableau_visuel(
    top_5_ecarts,
    f"{OUTPUT_DIR}/tableau_top_5_ecarts_arrondissements.png",
    "Top 5 des écarts entre prix affiché et prix réel par arrondissement"
)

# ================================
# GRAPHIQUE 2
# ================================

fig, ax = plt.subplots(figsize=(14, 7))

barres_dvf = ax.bar(
    df_ecart["arrondissement"].astype(str),
    df_ecart["ecart_pourcentage"]
)

plt.axhline(0, linewidth=1)

plt.title("Écart en % entre prix affiché et prix réel par arrondissement (DVF 2025)", fontsize=16)
plt.xlabel("Arrondissement")
plt.ylabel("Écart (%)")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/ecart_prix_annonce_reel_arrondissement.png", dpi=300)
plt.show()

# ================================
# 3. COMPARAISON PAR TRANCHE DE SURFACE
# ================================

query_surface = """
WITH dvf_surface AS (
    SELECT
        CASE
            WHEN surface_reelle_bati > 0 AND surface_reelle_bati <= 20 THEN '0-20 m²'
            WHEN surface_reelle_bati > 20 AND surface_reelle_bati <= 40 THEN '20-40 m²'
            WHEN surface_reelle_bati > 40 AND surface_reelle_bati <= 60 THEN '40-60 m²'
            WHEN surface_reelle_bati > 60 AND surface_reelle_bati <= 100 THEN '60-100 m²'
            WHEN surface_reelle_bati > 100 THEN '100 m² et +'
        END AS tranche_surface,
        AVG(prix_m2) AS prix_m2_dvf,
        COUNT(*) AS nb_observations_dvf
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND surface_reelle_bati IS NOT NULL
      AND annee_vente = 2025
    GROUP BY tranche_surface
),
scraping_surface AS (
    SELECT
        CASE
            WHEN surface > 0 AND surface <= 20 THEN '0-20 m²'
            WHEN surface > 20 AND surface <= 40 THEN '20-40 m²'
            WHEN surface > 40 AND surface <= 60 THEN '40-60 m²'
            WHEN surface > 60 AND surface <= 100 THEN '60-100 m²'
            WHEN surface > 100 THEN '100 m² et +'
        END AS tranche_surface,
        AVG(prix_m2) AS prix_m2_scraping,
        COUNT(*) AS nb_observations_scraping
    FROM golden_data_scraping
    WHERE prix_m2 IS NOT NULL
      AND surface IS NOT NULL
    GROUP BY tranche_surface
)
SELECT
    d.tranche_surface,
    d.prix_m2_dvf,
    s.prix_m2_scraping,
    d.nb_observations_dvf,
    s.nb_observations_scraping
FROM dvf_surface d
JOIN scraping_surface s
ON d.tranche_surface = s.tranche_surface
WHERE d.tranche_surface IS NOT NULL
ORDER BY
    CASE d.tranche_surface
        WHEN '0-20 m²' THEN 1
        WHEN '20-40 m²' THEN 2
        WHEN '40-60 m²' THEN 3
        WHEN '60-100 m²' THEN 4
        WHEN '100 m² et +' THEN 5
    END;
"""

with engine.connect() as conn:
    df_surface = pd.read_sql(text(query_surface), conn)

# ================================
# GRAPHIQUE 3
# ================================

fig, ax = plt.subplots(figsize=(12, 7))

x = range(len(df_surface))
width = 0.4

barres_dvf = ax.bar(
    [i - width / 2 for i in x],
    df_surface["prix_m2_dvf"],
    width=width,
    label="DVF 2025 - prix réel vendu"
)

barres_scraping = ax.bar(
    [i + width / 2 for i in x],
    df_surface["prix_m2_scraping"],
    width=width,
    label="Scraping - prix affiché"
)

ax.set_ylim(top=max(df_surface["prix_m2_dvf"].max(), df_surface["prix_m2_scraping"].max()) * 1.2)
annoter_effectifs(ax, barres_dvf, df_surface["nb_observations_dvf"])
annoter_effectifs(ax, barres_scraping, df_surface["nb_observations_scraping"])

ax.set_title("Comparaison du prix moyen au m² par tranche de surface (DVF 2025)", fontsize=16)
ax.set_xlabel("Tranche de surface")
ax.set_ylabel("Prix moyen au m² (€)")
ax.set_xticks(list(x))
ax.set_xticklabels(df_surface["tranche_surface"])
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/comparaison_prix_m2_surface.png", dpi=300)
plt.show()

# ================================
# 4. COMPARAISON PAR NOMBRE DE PIÈCES
# ================================

query_pieces = """
WITH dvf_pieces AS (
    SELECT
        CASE
            WHEN nombre_pieces_principales = 1 THEN '1 pièce'
            WHEN nombre_pieces_principales = 2 THEN '2 pièces'
            WHEN nombre_pieces_principales = 3 THEN '3 pièces'
            WHEN nombre_pieces_principales = 4 THEN '4 pièces'
            WHEN nombre_pieces_principales >= 5 THEN '5 pièces et +'
        END AS categorie_pieces,
        AVG(prix_m2) AS prix_m2_dvf,
        COUNT(*) AS nb_observations_dvf
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND nombre_pieces_principales IS NOT NULL
      AND nombre_pieces_principales >= 1
      AND annee_vente = 2025
    GROUP BY categorie_pieces
),
scraping_pieces AS (
    SELECT
        CASE
            WHEN nb_pieces = 1 THEN '1 pièce'
            WHEN nb_pieces = 2 THEN '2 pièces'
            WHEN nb_pieces = 3 THEN '3 pièces'
            WHEN nb_pieces = 4 THEN '4 pièces'
            WHEN nb_pieces >= 5 THEN '5 pièces et +'
        END AS categorie_pieces,
        AVG(prix_m2) AS prix_m2_scraping,
        COUNT(*) AS nb_observations_scraping
    FROM golden_data_scraping
    WHERE prix_m2 IS NOT NULL
      AND nb_pieces IS NOT NULL
      AND nb_pieces >= 1
    GROUP BY categorie_pieces
)
SELECT
    d.categorie_pieces,
    d.prix_m2_dvf,
    s.prix_m2_scraping,
    d.nb_observations_dvf,
    s.nb_observations_scraping
FROM dvf_pieces d
JOIN scraping_pieces s
ON d.categorie_pieces = s.categorie_pieces
WHERE d.categorie_pieces IS NOT NULL
ORDER BY
    CASE d.categorie_pieces
        WHEN '1 pièce' THEN 1
        WHEN '2 pièces' THEN 2
        WHEN '3 pièces' THEN 3
        WHEN '4 pièces' THEN 4
        WHEN '5 pièces et +' THEN 5
    END;
"""

with engine.connect() as conn:
    df_pieces = pd.read_sql(text(query_pieces), conn)

# ================================
# GRAPHIQUE 4
# ================================

fig, ax = plt.subplots(figsize=(12, 7))

x = range(len(df_pieces))
width = 0.4

barres_dvf = ax.bar(
    [i - width / 2 for i in x],
    df_pieces["prix_m2_dvf"],
    width=width,
    label="DVF 2025 - prix réel vendu"
)

barres_scraping = ax.bar(
    [i + width / 2 for i in x],
    df_pieces["prix_m2_scraping"],
    width=width,
    label="Scraping - prix affiché"
)

ax.set_ylim(top=max(df_pieces["prix_m2_dvf"].max(), df_pieces["prix_m2_scraping"].max()) * 1.2)
annoter_effectifs(ax, barres_dvf, df_pieces["nb_observations_dvf"])
annoter_effectifs(ax, barres_scraping, df_pieces["nb_observations_scraping"])

ax.set_title("Comparaison du prix moyen au m² par nombre de pièces (DVF 2025)", fontsize=16)
ax.set_xlabel("Nombre de pièces")
ax.set_ylabel("Prix moyen au m² (€)")
ax.set_xticks(list(x))
ax.set_xticklabels(df_pieces["categorie_pieces"])
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/comparaison_prix_m2_nombre_pieces.png", dpi=300)
plt.show()

# ================================
# 5. COMPARAISON DES MÉDIANES PAR ARRONDISSEMENT
# ================================

query_mediane_arrondissement = """
WITH scraping_clean AS (
    SELECT
        CAST(SUBSTRING(localisation FROM '750([0-9]{2})') AS INTEGER) AS arrondissement,
        prix_m2
    FROM golden_data_scraping
    WHERE prix_m2 IS NOT NULL
      AND localisation IS NOT NULL
      AND localisation LIKE '%750%'
),
dvf_mediane AS (
    SELECT
        arrondissement,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2) AS prix_m2_median_dvf,
        COUNT(*) AS nb_observations_dvf
    FROM dvf_paris_appartements
    WHERE prix_m2 IS NOT NULL
      AND arrondissement IS NOT NULL
      AND annee_vente = 2025
    GROUP BY arrondissement
),
scraping_mediane AS (
    SELECT
        arrondissement,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2) AS prix_m2_median_scraping,
        COUNT(*) AS nb_observations_scraping
    FROM scraping_clean
    WHERE arrondissement IS NOT NULL
    GROUP BY arrondissement
)
SELECT
    d.arrondissement,
    d.prix_m2_median_dvf,
    s.prix_m2_median_scraping,
    d.nb_observations_dvf,
    s.nb_observations_scraping
FROM dvf_mediane d
JOIN scraping_mediane s
ON d.arrondissement = s.arrondissement
ORDER BY d.arrondissement;
"""

with engine.connect() as conn:
    df_mediane_arr = pd.read_sql(text(query_mediane_arrondissement), conn)

# ================================
# GRAPHIQUE 5
# ================================

fig, ax = plt.subplots(figsize=(14, 7))

x = range(len(df_mediane_arr))
width = 0.4

barres_dvf = ax.bar(
    [i - width / 2 for i in x],
    df_mediane_arr["prix_m2_median_dvf"],
    width=width,
    label="DVF 2025 - médiane prix réel"
)

barres_scraping = ax.bar(
    [i + width / 2 for i in x],
    df_mediane_arr["prix_m2_median_scraping"],
    width=width,
    label="Scraping - médiane prix affiché"
)

ax.set_ylim(top=max(df_mediane_arr["prix_m2_median_dvf"].max(), df_mediane_arr["prix_m2_median_scraping"].max()) * 1.2)
annoter_effectifs(ax, barres_dvf, df_mediane_arr["nb_observations_dvf"])
annoter_effectifs(ax, barres_scraping, df_mediane_arr["nb_observations_scraping"])

ax.set_title("Comparaison du prix médian au m² par arrondissement (DVF 2025)", fontsize=16)
ax.set_xlabel("Arrondissement")
ax.set_ylabel("Prix médian au m² (€)")
ax.set_xticks(list(x))
ax.set_xticklabels(df_mediane_arr["arrondissement"])
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(f"{OUTPUT_DIR}/comparaison_prix_median_arrondissement.png", dpi=300)
plt.show()


print("Graphiques générés avec succès !")
print(f"Dossier : {OUTPUT_DIR}")

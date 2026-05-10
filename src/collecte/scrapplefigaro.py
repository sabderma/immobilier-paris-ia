from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import time
import re

# ---------------- Config navigateur ----------------
options = Options()
options.add_argument("--detach")

driver = webdriver.Chrome(options=options)

URL = "https://immobilier.lefigaro.fr/annonces/immobilier-vente-maison-paris.html?types=villa,chalet,appartement,duplex"

driver.get(URL)

# ---------------- Cookies ----------------
print("\nAccepte les cookies manuellement si besoin.\n")

# ---------------- CSV ----------------
with open("annonces_lefigaro_paris.csv", "w", newline="", encoding="utf-8") as f:

    w = csv.writer(f)

    w.writerow([
        "type",
        "prix",
        "prix_m2",
        "surface",
        "nb_pieces",
        "localisation",
        "details"
    ])

    page = 1

    while True:

        print(f"\n========== PAGE {page} ==========\n")

        input(
            "Va sur la page que tu veux scraper puis appuie sur ENTRÉE..."
        )

        # attendre les cartes
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR,
                    "ul.list-annonce li article.classified-card"
                ))
            )
        except:
            print("Aucune annonce trouvée.")
            continue

        cards = driver.find_elements(
            By.CSS_SELECTOR,
            "ul.list-annonce li article.classified-card"
        )

        print(f"{len(cards)} annonces trouvées.")

        for i, card in enumerate(cards, 1):

            type_bien = "non disponible"
            prix = "non disponible"
            prix_m2 = "non disponible"
            surface = "non disponible"
            nb_pieces = "non disponible"
            localisation = "non disponible"
            details = "non disponible"

            # ---------------- PRIX ----------------
            try:
                prix = card.find_element(
                    By.CSS_SELECTOR,
                    "div.main-price-wrapper span.main-price"
                ).text.strip()
            except NoSuchElementException:
                pass

            # ---------------- PRIX M² ----------------
            try:
                prix_m2 = card.find_element(
                    By.CSS_SELECTOR,
                    "div.price-per-m2-partner span.price-per-m2"
                ).text.strip()
            except NoSuchElementException:
                pass

            # ---------------- TYPE ----------------
            try:
                type_bien = card.find_element(
                    By.CSS_SELECTOR,
                    "p.classified-card-infos-estate-type"
                ).text.strip()
            except NoSuchElementException:
                pass

            # ---------------- SURFACE / PIÈCES ----------------
            try:
                items = card.find_elements(
                    By.CSS_SELECTOR,
                    "li.classified-card-infos-key-items"
                )

                for li in items:

                    t = li.text.strip()

                    if "m²" in t and surface == "non disponible":
                        m = re.search(
                            r"(\d+(?:[.,]\d+)?)\s*m²",
                            t
                        )

                        if m:
                            surface = m.group(0)

                    if "pièce" in t.lower() and nb_pieces == "non disponible":
                        m = re.search(
                            r"(\d+)\s*pièce",
                            t,
                            re.IGNORECASE
                        )

                        if m:
                            nb_pieces = f"{m.group(1)} pièces"

            except:
                pass

            # ---------------- LOCALISATION ----------------
            try:
                localisation = card.find_element(
                    By.CSS_SELECTOR,
                    "span.classified-card-infos-location"
                ).text.strip()

            except NoSuchElementException:
                pass

            # ---------------- DETAILS ----------------
            details_full = " ".join(card.text.split())

            details = (
                details_full[:160] + "…"
                if len(details_full) > 160
                else details_full
            )

            print(
                f"{i}. {type_bien} | {prix} | "
                f"{prix_m2} | {surface} | "
                f"{nb_pieces} | {localisation}"
            )

            w.writerow([
                type_bien,
                prix,
                prix_m2,
                surface,
                nb_pieces,
                localisation,
                details
            ])

        rep = input(
            "\nTape 'q' pour arrêter ou ENTRÉE pour continuer : "
        )

        if rep.lower() == "q":
            break

        page += 1

driver.quit()

print("\nScraping terminé — fichier : annonces_lefigaro_paris.csv")
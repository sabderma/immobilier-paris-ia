"""Scraper des annonces immobilieres Century 21 pour Paris.

Ce script automatise la navigation avec Selenium, recupere les annonces page par
page et sauvegarde les donnees brutes dans un CSV.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv, time, re

options = Options()
options.add_argument("--detach")
driver = webdriver.Chrome(options=options)

# Page de recherche Century 21 pour achats maison/appartement a Paris.
url = "https://www.century21.fr/annonces/f/achat-maison-appartement/v-paris/"
driver.get(url)

with open("data/raw/scraping/annonces_century21_paris.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["type", "prix", "surface", "nb_pieces", "localisation", "details"])

    page = 1
    MAX_PAGES = 100  

    while page <= MAX_PAGES:
        print(f"\n========== PAGE {page} ==========\n")

        # attendre les cartes
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR,
                "div.js-the-list-of-properties-list-property"
            ))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, "div.js-the-list-of-properties-list-property")
        print(f"{len(cards)} annonces trouvées sur cette page.\n")

        for i, card in enumerate(cards, 1):
            # Valeurs par defaut pour garder une structure CSV stable.
            type_bien = "non disponible"
            prix = "non disponible"
            surface = "non disponible"
            nb_pieces = "non disponible"
            localisation = "non disponible"
            details = "non disponible"

            # ---- PRIX ----
            for sel in [
                "div.c-text-theme-heading-1.tw-whitespace-nowrap",
                "div.c-text-theme-heading-1"
            ]:
                try:
                    t = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                    if t:
                        prix = t
                        break
                except NoSuchElementException:
                    pass

            # ---- TYPE ----
            try:
                type_bien = card.find_element(
                    By.CSS_SELECTOR,
                    "div.c-text-theme-heading-3.tw-leading-none.tw-text-c21-grey-darker"
                ).text.strip()
            except NoSuchElementException:
                try:
                    type_bien = card.find_element(By.CSS_SELECTOR, "div.c-text-theme-heading-3").text.strip()
                except NoSuchElementException:
                    pass

            # ---- DÉTAILS ----
            try:
                details = card.find_element(
                    By.CSS_SELECTOR,
                    "div.c-text-theme-base.tw-truncate-safe"
                ).text.strip()
            except NoSuchElementException:
                pass

            # ---- REGEX sur tout le bloc ----
            bloc_txt = card.text

            m = re.search(r"(\d+)\s*pièce", bloc_txt, re.IGNORECASE)
            if m:
                nb_pieces = f"{m.group(1)} pièces"

            m = re.search(r"(\d+)\s*(?:m²|m2)", bloc_txt, re.IGNORECASE)
            if m:
                surface = f"{m.group(1)} m²"

            m = re.search(r"(PARIS\s*\d{5})", bloc_txt, re.IGNORECASE)
            if m:
                localisation = m.group(1).upper()
            else:
                m2 = re.search(r"(PARIS\b[^\n]*)", bloc_txt, re.IGNORECASE)
                if m2:
                    localisation = m2.group(1).strip()

            print(f"{i}. {type_bien} | {prix} | {surface} | {nb_pieces} | {localisation} | {details}")
            writer.writerow([type_bien, prix, surface, nb_pieces, localisation, details])

        # ---------- PAGINATION ----------
        # scroll jusqu’à la pagination pour être sûr qu’elle est visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.8)

        try:
            
            next_btn = driver.find_element(By.CSS_SELECTOR, "a[aria-label='next']")
            driver.execute_script("arguments[0].click();", next_btn)

            print("Passage à la page suivante...")

            # attendre chargement nouvelle page
            time.sleep(3)
        except NoSuchElementException:
            print(" Pas de bouton Suivant — fin.")
            break

        page += 1

print("\n Scraping terminé.")
driver.quit()

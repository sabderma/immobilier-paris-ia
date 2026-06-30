"""Scraper des annonces immobilieres La Foret pour Paris.

Ce fichier charge la page de recherche, descend jusqu'en bas pour afficher les
annonces, puis extrait les champs utiles dans un CSV brut.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import re
import time

options = Options()
options.add_argument("--detach")
driver = webdriver.Chrome(options=options)

# URL de recherche La Foret pour maisons et appartements sur Paris.
URL = "https://www.laforet.com/acheter/rechercher?filter%5Btypes%5D%5B%5D=house&filter%5Btypes%5D%5B%5D=apartment&filter%5Bcities%5D%5B%5D=&filter%5Bcities%5D%5B%5D=75056&filter%5Barea%5D=&filter%5Bmin%5D=&filter%5Bmax%5D=&filter%5Bsurface%5D=0"
driver.get(URL)

# ------------------ Cookies ------------------
try:
    WebDriverWait(driver, 8).until(
        EC.element_to_be_clickable(
            (By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        )
    ).click()
    print("Cookies acceptés.")
except:
    print("Cookies déjà acceptés ou bouton non présent.")

# ------------------ Scroll automatique ------------------
print("Scroll automatique en cours...")

last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("Bas de page atteint.")
        break
    last_height = new_height

time.sleep(1)

# ------------------ Récupération des annonces ------------------
cards = driver.find_elements(By.CSS_SELECTOR, "article.min-w-0")

print(f"\nTotal d'annonces détectées après scroll : {len(cards)}\n")

with open("data/raw/scraping/annonces_laforet_paris_complet.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["type", "prix", "surface", "nb_pieces", "localisation", "details"])

    for i, card in enumerate(cards, 1):
        # Chaque champ est initialise pour garder une ligne CSV meme si le site manque une info.
        type_bien = "non disponible"
        prix = "non disponible"
        surface = "non disponible"
        nb_pieces = "non disponible"
        localisation = "non disponible"
        details = "non disponible"

        # ------------------ TYPE ------------------
        for sel in [
            "h3.text-primary.font-semibold",
            "h3",
            "div.text-primary.font-semibold"
        ]:
            try:
                brut = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                if brut:
                    type_bien = brut.split("\n")[0].strip()
                    type_bien = type_bien.split("•")[0].strip()
                    break
            except:
                pass

        # ------------------ PRIX ------------------
        for sel in [
            "span.text-tertiary.font-bold",
            "div.text-tertiary.font-bold",
            "span.font-bold.text-right"
        ]:
            try:
                txt = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                if txt:
                    prix = txt
                    break
            except:
                pass

        # ------------------ LOCALISATION ------------------
        for sel in [
            "span.font-bold.text-gray-600",
            "span.text-gray-600.font-bold",
            "div.text-gray-600.font-bold"
        ]:
            try:
                txt = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                if txt:
                    localisation = txt
                    break
            except:
                pass

        # ------------------ CARACTÉRISTIQUES ------------------
        try:
            caracs = card.find_element(By.CSS_SELECTOR, "div.text.flex.flex-wrap").text
        except:
            caracs = card.text

        m = re.search(r"(\d+)\s*(?:m²|m2)", caracs, re.I)
        if m:
            surface = f"{m.group(1)} m²"

        m = re.search(r"(\d+)\s*pièce", caracs, re.I)
        if m:
            nb_pieces = f"{m.group(1)} pièces"

        # ------------------ DÉTAILS ------------------
        try:
            txt = card.find_element(By.CSS_SELECTOR, "div.text.truncate").text.strip()
            if txt:
                details = txt
        except:
            pass

        print(
            f"{i}. {type_bien} | {prix} | {surface} | "
            f"{nb_pieces} | {localisation} | {details}"
        )

        w.writerow([
            type_bien,
            prix,
            surface,
            nb_pieces,
            localisation,
            details
        ])

print("\nScraping terminé — fichier : annonces_laforet_paris_complet.csv")
driver.quit()

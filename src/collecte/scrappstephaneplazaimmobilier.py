"""Scraper des annonces Stephane Plaza Immobilier pour Paris.

Le script charge toutes les annonces disponibles via le scroll, extrait les
informations visibles, puis les ecrit dans un fichier CSV brut.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import csv, time, re

# ------------------ Config navigateur ------------------
options = Options()
options.add_argument("--detach")    
driver = webdriver.Chrome(options=options)

# Page cible : achats appartement/maison dans le departement Paris.
url = "https://www.stephaneplazaimmobilier.com/acheter/departement/paris_75/appartement,maison/"
driver.get(url)

# ------------------ Cookies ------------------
try:
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2"))
    ).click()
except Exception:
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

# ------------------ Scrape & CSV ------------------
with open("data/raw/scraping/annonces_plaza_paris.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["type", "prix", "surface", "nb_pieces", "localisation", "details"])

    cards = driver.find_elements(By.CSS_SELECTOR, "div.room.purchase")
    print(f"\nTotal final : {len(cards)} cartes à parser\n")

    for i, card in enumerate(cards, 1):
        # Les champs commencent en "non disponible" si le site ne donne pas la valeur.
        type_bien = "non disponible"
        prix = "non disponible"
        surface = "non disponible"
        nb_pieces = "non disponible"
        localisation = "non disponible"
        details = "non disponible"

        # ---- PRIX (span.card-right) ----
        try:
            txt = card.find_element(By.CSS_SELECTOR, "span.card-right").text.strip()
            if txt:
                prix = txt
        except NoSuchElementException:
            pass

        # ---- LOCALISATION (span.card-left.uppercase) ----
        try:
            txt = card.find_element(By.CSS_SELECTOR, "span.card-left.uppercase").text.strip()
            if txt:
                localisation = txt
        except NoSuchElementException:
            pass

        # ---- TITRE (h3.title-wrap) pour type/surface/pièces ----
        titre = ""
        try:
            titre = card.find_element(By.CSS_SELECTOR, "h3.title-wrap").text.strip()
        except NoSuchElementException:
            pass

        bloc_txt = titre or card.text

        # type
        if re.search(r"appartement", bloc_txt, re.I):
            type_bien = "Appartement"
        elif re.search(r"maison", bloc_txt, re.I):
            type_bien = "Maison"

        # nb pièces
        m = re.search(r"(\d+)\s*pi[eè]ce", bloc_txt, re.I)
        if m:
            nb_pieces = f"{m.group(1)} pièces"

        # surface (gère virgule/point)
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*m(?:²|2)", bloc_txt, re.I)
        if m:
            surface = f"{m.group(1).replace(',', '.')} m²"

        # ---- DÉTAILS ----
        try:
            p = card.find_element(By.CSS_SELECTOR, "p")
            txt = p.text.strip()
            if txt:
                details = txt
        except NoSuchElementException:
            pass

        print(f"{i}. {type_bien} | {prix} | {surface} | {nb_pieces} | {localisation} | {details[:80]}{'…' if len(details)>80 else ''}")
        writer.writerow([type_bien, prix, surface, nb_pieces, localisation, details])

print("\nScraping terminé — toutes les annonces chargées et exportées dans 'annonces_plaza_paris.csv'.")
driver.quit()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
import time
import re

# ---------------- Config navigateur ----------------
options = Options()
options.add_argument("--detach")
driver = webdriver.Chrome(options=options)

URL = "https://immobilier.lefigaro.fr/annonces/immobilier-vente-maison-paris.html?types=villa,chalet,appartement,duplex"
driver.get(URL)
time.sleep(3)

# ---------------- Cookies ----------------
cookie_accepted = False

try:
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"{len(iframes)} iframe(s) détectée(s).")
    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accepter') or contains(., 'accepter') or contains(., 'Tout accepter') or contains(., \"J'accepte\")]"))
            )
            btn.click()
            print("Cookies acceptés dans l'iframe.")
            cookie_accepted = True
            driver.switch_to.default_content()
            break
        except:
            driver.switch_to.default_content()
            continue
except:
    pass

if not cookie_accepted:
    input("Accepte les cookies manuellement puis appuie sur ENTRÉE...")

time.sleep(2)

# ---------------- CSV ----------------
with open("data/raw/scraping/annonces_lefigaro_paris.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["type", "prix", "prix_m2", "surface", "nb_pieces", "localisation", "details"])

    page = 1

    while True:
        print(f"\n========== PAGE {page} ==========\n")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR,
                    "ul.list-annonce li article.classified-card"
                ))
            )
        except TimeoutException:
            print("Aucune annonce trouvée sur cette page, arrêt.")
            break

        time.sleep(2)

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

            try:
                prix = card.find_element(By.CSS_SELECTOR, "div.main-price-wrapper span.main-price").text.strip()
            except NoSuchElementException:
                pass

            try:
                prix_m2 = card.find_element(By.CSS_SELECTOR, "div.price-per-m2-partner span.price-per-m2").text.strip()
            except NoSuchElementException:
                pass

            try:
                type_bien = card.find_element(By.CSS_SELECTOR, "p.classified-card-infos-estate-type").text.strip()
            except NoSuchElementException:
                pass

            try:
                items = card.find_elements(By.CSS_SELECTOR, "li.classified-card-infos-key-items")
                for li in items:
                    t = li.text.strip()
                    if "m²" in t and surface == "non disponible":
                        m = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", t)
                        if m:
                            surface = m.group(0)
                    if "pièce" in t.lower() and nb_pieces == "non disponible":
                        m = re.search(r"(\d+)\s*pièce", t, re.IGNORECASE)
                        if m:
                            nb_pieces = f"{m.group(1)} pièces"
            except:
                pass

            try:
                localisation = card.find_element(By.CSS_SELECTOR, "span.classified-card-infos-location").text.strip()
            except NoSuchElementException:
                pass

            details_full = " ".join(card.text.split())
            details = details_full[:160] + "…" if len(details_full) > 160 else details_full

            print(f"{i}. {type_bien} | {prix} | {prix_m2} | {surface} | {nb_pieces} | {localisation}")
            w.writerow([type_bien, prix, prix_m2, surface, nb_pieces, localisation, details])

        # ---------------- PAGE SUIVANTE ----------------
        # La pagination utilise des <button> dans ul.pagination
        try:
            # Scroll jusqu'à la pagination
            pagination = driver.find_element(By.CSS_SELECTOR, "nav.pagination-list")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pagination)
            time.sleep(1)

            # Cherche le bouton "suivant" — rel="next" ou title contenant "suivante"
            next_btn = None
            for sel in [
                "button[rel='next']",
                "button[title*='suivante']",
                "button[title*='Suivante']",
                "nav.pagination-list button:not([disabled]):last-child",
            ]:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if "disabled" not in (btn.get_attribute("class") or ""):
                        next_btn = btn
                        break
                except:
                    continue

            # Fallback : bouton suivant dans ul.pagination (le numéro de page actuel + 1)
            if next_btn is None:
                current_btn = driver.find_element(By.CSS_SELECTOR, "ul.pagination button.link--current")
                current_text = current_btn.text.strip()
                all_page_btns = driver.find_elements(By.CSS_SELECTOR, "ul.pagination button.link")
                for btn in all_page_btns:
                    if btn.text.strip() == str(int(current_text) + 1):
                        next_btn = btn
                        break

            if next_btn is None:
                print("Dernière page atteinte.")
                break

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            time.sleep(1)
            try:
                next_btn.click()
            except:
                driver.execute_script("arguments[0].click();", next_btn)

            page += 1
            time.sleep(4)

        except NoSuchElementException:
            print("Pagination introuvable : fin du scraping.")
            break

driver.quit()
print("\nScraping terminé — fichier : annonces_lefigaro_paris.csv")
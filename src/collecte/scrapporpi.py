from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
import time
import re

options = Options()
options.add_argument("--detach")
driver = webdriver.Chrome(options=options)

url = "https://www.orpi.com/recherche/buy?transaction=buy&realEstateTypes%5B0%5D=maison&realEstateTypes%5B1%5D=appartement&locations%5B0%5D%5Bvalue%5D=paris"
driver.get(url)

try:
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
    ).click()
except:
    print("Cookies déjà acceptés ou bouton non présent.")


def get_next_button():
    """Essaie plusieurs sélecteurs pour trouver le bouton Suivant."""
    selectors = [
        "li.c-pagination__item.c-pagination__item--next a",
        "a[aria-label='Page suivante']",
        "a[rel='next']",
        ".c-pagination__item--next a",
        "a.c-pagination__link--next",
    ]
    for sel in selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            return btn
        except NoSuchElementException:
            continue

    # Fallback : cherche un lien contenant "suivant" dans le texte
    try:
        btn = driver.find_element(By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'suivant')]")
        return btn
    except NoSuchElementException:
        return None


def is_button_disabled(btn):
    """Vérifie si le bouton ou son parent est désactivé."""
    try:
        parent = btn.find_element(By.XPATH, "./..")
        classes = parent.get_attribute("class") or ""
        if "disabled" in classes or "is-disabled" in classes:
            return True
    except:
        pass
    btn_class = btn.get_attribute("class") or ""
    if "disabled" in btn_class or "is-disabled" in btn_class:
        return True
    if btn.get_attribute("aria-disabled") == "true":
        return True
    return False


with open("data/raw/scraping/annonces_orpi_paris.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["type", "prix", "prix_m2", "surface", "nb_pieces", "localisation", "details"])

    page = 1
    while page < 100:
        print(f"\n========== PAGE {page} ==========\n")

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR,
                    "li.o-grid__col.u-flex.u-flex-column.c-results__list__item"
                ))
            )
        except TimeoutException:
            print("Timeout : aucune annonce détectée sur cette page.")
            break

        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        results = driver.find_elements(
            By.CSS_SELECTOR,
            "li.o-grid__col.u-flex.u-flex-column.c-results__list__item"
        )

        print(f"{len(results)} annonces trouvées sur cette page.\n")

        for i, result in enumerate(results, 1):
            type_bien = "non disponible"
            prix = "non disponible"
            prix_m2 = "non disponible"
            surface = "non disponible"
            nb_pieces = "non disponible"
            localisation = "non disponible"
            details = "non disponible"

            # ---------- PRIX ----------
            try:
                prix = result.find_element(
                    By.CSS_SELECTOR,
                    "span.u-text-bold.c-estate-thumb__price-tag__price.u-h4"
                ).text.strip()
            except NoSuchElementException:
                pass

            # ---------- PRIX / m² ----------
            try:
                prix_m2 = result.find_element(
                    By.CSS_SELECTOR,
                    "div.c-estate-thumb_price-sqm"
                ).text.strip()
            except NoSuchElementException:
                pass

            # ---------- INFOS ----------
            try:
                infos = result.find_element(
                    By.CSS_SELECTOR,
                    "div.u-mr-sm.c-estate-thumb__infos__estate.u-flex-item-fluid"
                )

                try:
                    b_tag = infos.find_element(By.CSS_SELECTOR, "b")
                    b_text = b_tag.text.strip()

                    match_pieces = re.search(r"(\d+\s*pièce[s]?)", b_text, re.IGNORECASE)
                    if match_pieces:
                        nb_pieces = match_pieces.group(1).strip()

                    match_surface = re.search(r"(\d+\s*(?:m²|m2))", b_text, re.IGNORECASE)
                    if match_surface:
                        surface = match_surface.group(1).strip()

                    if "appartement" in b_text.lower():
                        type_bien = "Appartement"
                    elif "maison" in b_text.lower():
                        type_bien = "Maison"

                except NoSuchElementException:
                    pass

                try:
                    localisation = infos.find_element(
                        By.CSS_SELECTOR,
                        "span.u-mt-n.c-estate-thumb__infos__location"
                    ).text.strip()
                except NoSuchElementException:
                    pass

            except NoSuchElementException:
                pass

            # ---------- DÉTAILS ----------
            try:
                tags_container = result.find_element(By.CSS_SELECTOR, "div.c-estate-thumb__tags")
                tag_spans = tags_container.find_elements(By.CSS_SELECTOR, "span.c-tag")
                tags = [span.text.strip() for span in tag_spans if span.text.strip()]
                if tags:
                    details = ", ".join(tags)
            except NoSuchElementException:
                pass

            print(f"{i}. {type_bien} | {prix} | {surface} | {nb_pieces} | {localisation}")
            writer.writerow([type_bien, prix, prix_m2, surface, nb_pieces, localisation, details])

        # ---------- PAGE SUIVANTE ----------
        next_btn = get_next_button()

        if next_btn is None:
            print("Bouton 'Suivant' introuvable : fin du scraping.")
            break

        if is_button_disabled(next_btn):
            print("Bouton 'Suivant' désactivé : dernière page atteinte.")
            break

        # Scroll jusqu'au bouton puis clic
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        time.sleep(1)
        try:
            next_btn.click()
        except:
            # Si le clic normal échoue, on force via JavaScript
            driver.execute_script("arguments[0].click();", next_btn)

        page += 1
        time.sleep(4)

print("\nScraping terminé — toutes les pages ont été parcourues.")
driver.quit()
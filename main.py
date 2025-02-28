import os
import re
import json
import logging
import datetime
import time
import asyncio
from flask import Flask, Response
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from telegram import Bot
from telegram.constants import ParseMode

# Import per Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ------------------------ CONFIGURAZIONE ------------------------
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
TELEGRAM_CHAT_ID = "-1002290458283"
ASSOCIATE_TAG = "new1707-21"

# File per memorizzare le offerte già inviate (evitare duplicati)
SENT_OFFERS_FILE = "sent_offers.json"

# Inizializza il bot Telegram e l'app Flask
bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Elenco delle fonti Amazon da cui recuperare le offerte
HTML_SOURCES = [
    "https://www.amazon.it/gp/goldbox",
    "https://www.amazon.it/gp/bestsellers",
    "https://www.amazon.it/gp/movers-and-shakers",
    "https://www.amazon.it/gp/most-gifted",
    "https://www.amazon.it/gp/most-wished-for",
    "https://www.amazon.it/gp/new-releases"
    # Puoi aggiungere ulteriori URL se necessario.
]

# ------------------------ FUNZIONI UTILI ------------------------

def get_dynamic_content(url, timeout=15):
    """
    Avvia Selenium in modalità headless per caricare la pagina e restituire l'HTML
    dopo che il contenuto dinamico è stato caricato.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)
    except Exception as e:
        logger.error(f"Timeout o errore nel caricamento dinamico di {url}: {e}")
    html = driver.page_source
    driver.quit()
    return html

def load_sent_offers():
    """Carica dal file la lista degli URL delle offerte già inviate."""
    if os.path.exists(SENT_OFFERS_FILE):
        try:
            with open(SENT_OFFERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_sent_offers(sent_offers):
    """Salva la lista aggiornata delle offerte inviate su file."""
    with open(SENT_OFFERS_FILE, "w") as f:
        json.dump(sent_offers, f)

def scrape_amazon_deals(url):
    """
    Esegue lo scraping di una pagina Amazon per ottenere le offerte.
    Ritorna una lista di dizionari con: title, link, discount, pubDate.
    Utilizza Selenium per ottenere l'HTML dinamico e diversi selettori per ampliare la ricerca.
    """
    logger.info(f"Scraping {url} ...")
    html = get_dynamic_content(url)
    soup = BeautifulSoup(html, "html.parser")
    deals = []

    selectors = [
        {'tag': 'div', 'attrs': {"data-testid": "deal-card"}},
        {'tag': 'div', 'attrs': {"class": "DealContent"}},
        {'tag': 'li', 'attrs': {"class": re.compile(r"zg-item-immersion")}},
        {'tag': 'li', 'attrs': {"class": re.compile(r"a-carousel-card", re.IGNORECASE)}},
        {'tag': 'div', 'attrs': {"class": re.compile(r"offer", re.IGNORECASE)}},
    ]
    deal_containers = []
    for sel in selectors:
        found = soup.find_all(sel['tag'], attrs=sel['attrs'])
        if found:
            logger.info(f"{url} => Trovati {len(found)} elementi con selettore: tag {sel['tag']}, attrs {sel['attrs']}")
        deal_containers.extend(found)
    deal_containers = list({id(el): el for el in deal_containers}.values())
    logger.info(f"{url} => Numero totale di container trovati: {len(deal_containers)}")

    for container in deal_containers:
        try:
            title = None
            title_selectors = [
                {'tag': 'span', 'attrs': {"class": re.compile(r"a-size-medium")}},
                {'tag': 'span', 'attrs': {"class": re.compile(r"title", re.IGNORECASE)}},
            ]
            for ts in title_selectors:
                t_tag = container.find(ts['tag'], attrs=ts['attrs'])
                if t_tag:
                    title = t_tag.get_text(strip=True)
                    break
            if not title:
                continue

            a_tag = container.find("a", href=True)
            if not a_tag:
                continue
            href = a_tag["href"]
            link = "https://www.amazon.it" + href if href.startswith("/") else href
            if "tag=" not in link:
                link += "&tag=" + ASSOCIATE_TAG if "?" in link else "?tag=" + ASSOCIATE_TAG

            discount = 0
            discount_selectors = [
                {'tag': 'span', 'attrs': {"class": re.compile(r"savings", re.IGNORECASE)}},
                {'tag': 'span', 'attrs': {"class": re.compile(r"dealBadge", re.IGNORECASE)}},
            ]
            for ds in discount_selectors:
                d_tag = container.find(ds['tag'], attrs=ds['attrs'])
                if d_tag:
                    discount_text = d_tag.get_text(strip=True)
                    discount_match = re.search(r'(\d{1,3})\s*%', discount_text)
                    if discount_match:
                        discount = int(discount_match.group(1))
                        break

            pubDate = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

            deals.append({
                "title": title,
                "link": link,
                "discount": discount,
                "pubDate": pubDate
            })
        except Exception as e:
            logger.error(f"Errore nell'estrazione di un'offerta da {url}: {e}")
            continue

    return deals

def gather_all_deals():
    """
    Esegue lo scraping su tutte le fonti HTML definite in HTML_SOURCES,
    unifica le offerte in un'unica lista, rimuove duplicati e ordina per sconto.
    """
    all_deals = []
    for source_url in HTML_SOURCES:
        deals = scrape_amazon_deals(source_url)
        all_deals.extend(deals)
    unique_deals = {}
    for deal in all_deals:
        unique_deals[deal["link"]] = deal
    final_deals = list(unique_deals.values())
    final_deals.sort(key=lambda d: d["discount"], reverse=True)
    return final_deals

def generate_rss_feed(deals):
    """
    Genera un feed RSS in formato XML a partire dalla lista di offerte.
    """
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Migliori Offerte Amazon (Multi-Fonte)"
    ET.SubElement(channel, "link").text = "https://www.amazon.it"
    ET.SubElement(channel, "description").text = (
        "Feed RSS dinamico con le migliori offerte e sconti da Amazon (più fonti) aggiornate in tempo reale."
    )
    ET.SubElement(channel, "language").text = "it-it"
    
    for deal in deals:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"{deal['title']} - Sconto del {deal['discount']}%"
        ET.SubElement(item, "link").text = deal["link"]
        ET.SubElement(item, "description").text = (
            f"Offerta: {deal['title']} con uno sconto del {deal['discount']}% su Amazon."
        )
        ET.SubElement(item, "pubDate").text = deal["pubDate"]
        ET.SubElement(item, "guid").text = deal["link"]

    rough_string = ET.tostring(rss, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

async def send_telegram_message(message):
    """
    Invia il messaggio formattato in Markdown al canale/gruppo Telegram.
    """
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN_V2)
        logger.info("Messaggio inviato con successo!")
    except Exception as e:
        logger.error(f"Errore durante l'invio del messaggio: {e}")

# ------------------------ ENDPOINTS FLASK ------------------------
@app.route("/")
def home():
    return "🤖 Bot attivo - Multi-Fonte (Selenium)"

@app.route("/rss")
def rss_feed():
    """
    Endpoint che restituisce il feed RSS dinamico unificando le offerte da più fonti.
    """
    deals = gather_all_deals()
    if not deals:
        return Response("Nessuna offerta trovata", status=200, mimetype="text/plain")
    rss_xml = generate_rss_feed(deals)
    return Response(rss_xml, mimetype="application/rss+xml")

@app.route("/fetch_offer")
def fetch_offer():
    """
    Endpoint da pingare (es. ogni 60 minuti) che:
      - Seleziona la migliore offerta (con sconto maggiore) non ancora inviata.
      - La invia su Telegram.
      - Registra l'offerta inviata per non ripeterla.
    """
    deals = gather_all_deals()
    if not deals:
        logger.info("Nessuna offerta trovata.")
        return "Nessuna offerta trovata."

    sent_offers = load_sent_offers()
    new_deals = [deal for deal in deals if deal["link"] not in sent_offers]
    if not new_deals:
        logger.info("Nessuna nuova offerta da inviare.")
        return "Nessuna nuova offerta da inviare."

    best_deal = new_deals[0]
    message = (
        f"🔥 *{best_deal['title']}*\n"
        f"💰 *Sconto: {best_deal['discount']}%*\n"
        f"🔗 [Acquista ora]({best_deal['link']})"
    )
    asyncio.run(send_telegram_message(message))
    sent_offers.append(best_deal["link"])
    save_sent_offers(sent_offers)
    logger.info(f"Offerta inviata: {best_deal['title']}")
    return "Offerta inviata!"

# ------------------------ AVVIO DELL'APPLICAZIONE ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

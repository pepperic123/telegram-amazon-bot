import os
import re
import json
import logging
import datetime
import requests
import asyncio
from flask import Flask, Response
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from telegram import Bot
from telegram.constants import ParseMode

# ------------------------ CONFIGURAZIONE ------------------------
# Dati Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
TELEGRAM_CHAT_ID = "-1002290458283"

# Associate Tag Amazon
ASSOCIATE_TAG = "new1707-21"

# File per memorizzare le offerte già inviate (evitare duplicati)
SENT_OFFERS_FILE = "sent_offers.json"

# Inizializza il bot Telegram e l'app Flask
bot = Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------ FUNZIONI UTILI ------------------------
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

def scrape_amazon_deals():
    """
    Esegue lo scraping della pagina Amazon Gold Box per ottenere le offerte.
    Ritorna una lista di dizionari con: title, link, discount e pubDate.
    """
    url = "https://www.amazon.it/gp/goldbox"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        logger.error(f"Errore durante la richiesta ad Amazon: {e}")
        return []
    if response.status_code != 200:
        logger.error(f"Errore nello scraping, status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    deals = []

    # Prova a individuare i container delle offerte con un attributo 'data-testid'
    deal_containers = soup.find_all("div", {"data-testid": "deal-card"})
    if not deal_containers:
        deal_containers = soup.find_all("div", class_="DealContent")
    logger.info(f"Numero di container trovati: {len(deal_containers)}")

    for container in deal_containers:
        try:
            # Estrazione del titolo (ricerca un tag <span> con classe tipo "a-size-medium")
            title_tag = container.find("span", class_=re.compile("a-size-medium"))
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            # Estrazione del link: ricerca il primo tag <a> con attributo href
            a_tag = container.find("a", href=True)
            if not a_tag:
                continue
            href = a_tag["href"]
            link = "https://www.amazon.it" + href if href.startswith("/") else href

            # Aggiungi l'associate tag se non presente nell'URL
            if "tag=" not in link:
                link += "&tag=" + ASSOCIATE_TAG if "?" in link else "?tag=" + ASSOCIATE_TAG

            # Estrazione della percentuale di sconto (es. "40% OFF")
            discount_tag = container.find("span", class_=re.compile("savings"))
            discount_text = discount_tag.get_text(strip=True) if discount_tag else ""
            discount_match = re.search(r'(\d{1,3})\s*%', discount_text)
            discount = int(discount_match.group(1)) if discount_match else 0

            pubDate = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

            deals.append({
                "title": title,
                "link": link,
                "discount": discount,
                "pubDate": pubDate
            })
        except Exception as e:
            logger.error(f"Errore nell'estrazione di un'offerta: {e}")
            continue

    # Ordina le offerte per sconto in ordine decrescente
    deals = sorted(deals, key=lambda d: d["discount"], reverse=True)
    return deals

def generate_rss_feed(deals):
    """
    Genera un feed RSS in formato XML a partire dalla lista delle offerte.
    """
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    # Informazioni sul canale RSS
    ET.SubElement(channel, "title").text = "Migliori Offerte Amazon"
    ET.SubElement(channel, "link").text = "https://www.amazon.it"
    ET.SubElement(channel, "description").text = (
        "Feed RSS dinamico con le migliori offerte e sconti da Amazon aggiornate in tempo reale."
    )
    ET.SubElement(channel, "language").text = "it-it"
    
    # Crea un item per ogni offerta
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
    return "🤖 Bot attivo"

@app.route("/rss")
def rss_feed():
    """
    Endpoint che restituisce il feed RSS dinamico.
    """
    deals = scrape_amazon_deals()
    if not deals:
        return Response("Nessuna offerta trovata", status=200, mimetype="text/plain")
    rss_xml = generate_rss_feed(deals)
    return Response(rss_xml, mimetype="application/rss+xml")

@app.route("/fetch_offer")
def fetch_offer():
    """
    Endpoint da pingare (es. ogni 60 minuti tramite UptimeRobot) che:
      - Seleziona l'offerta migliore (con sconto maggiore) non ancora inviata.
      - La invia tramite Telegram.
      - Registra l'offerta inviata per non ripeterla.
    """
    deals = scrape_amazon_deals()
    if not deals:
        logger.info("Nessuna offerta trovata.")
        return "Nessuna offerta trovata."

    sent_offers = load_sent_offers()
    # Filtra le offerte non ancora inviate
    new_deals = [deal for deal in deals if deal["link"] not in sent_offers]
    if not new_deals:
        logger.info("Nessuna nuova offerta da inviare.")
        return "Nessuna nuova offerta da inviare."

    # Seleziona la migliore offerta (la prima, poiché ordinata per sconto decrescente)
    best_deal = new_deals[0]
    message = (
        f"🔥 *{best_deal['title']}*\n"
        f"💰 *Sconto: {best_deal['discount']}%*\n"
        f"🔗 [Acquista ora]({best_deal['link']})"
    )
    asyncio.run(send_telegram_message(message))

    # Registra l'offerta come inviata per evitare duplicati
    sent_offers.append(best_deal["link"])
    save_sent_offers(sent_offers)
    logger.info(f"Offerta inviata: {best_deal['title']}")
    return "Offerta inviata!"

# ------------------------ AVVIO DELL'APPLICAZIONE ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

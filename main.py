import os
import json
import logging
import feedparser
import re
import asyncio
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
TELEGRAM_CHAT_ID = "-1002290458283"

# URL del feed RSS (sostituisci con quello reale)
RSS_FEED_URL = "https://www.example.com/rss"

# File per memorizzare le offerte già inviate
SENT_OFFERS_FILE = "sent_offers.json"

# Crea l'app Flask e il bot Telegram
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def load_sent_offers():
    """Carica la lista delle offerte già inviate da un file JSON."""
    if os.path.exists(SENT_OFFERS_FILE):
        try:
            with open(SENT_OFFERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_sent_offers(sent_offers):
    """Salva la lista aggiornata delle offerte inviate."""
    with open(SENT_OFFERS_FILE, "w") as f:
        json.dump(sent_offers, f)

def extract_discount(text):
    """
    Cerca nel testo un pattern che rappresenta una percentuale, ad esempio "50%".
    Restituisce il valore numerico dello sconto oppure 0 se non trovato.
    """
    match = re.search(r'(\d{1,3})\s*%', text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return 0
    return 0

def get_best_offer():
    """
    Analizza il feed RSS, esclude le offerte già inviate e seleziona quella
    con il maggior sconto (basato sull'estrazione da title e description).
    """
    feed = feedparser.parse(RSS_FEED_URL)
    sent_offers = load_sent_offers()
    best_offer = None
    highest_discount = 0

    for entry in feed.entries:
        # Usa 'id' se presente, altrimenti il link come identificativo
        offer_id = entry.get("id", entry.get("link"))
        if offer_id in sent_offers:
            continue

        # Combina title e description per cercare la percentuale di sconto
        content = f"{entry.get('title', '')} {entry.get('description', '')}"
        discount = extract_discount(content)
        if discount > highest_discount:
            highest_discount = discount
            best_offer = entry

    return best_offer

async def send_telegram_message(message):
    """
    Invia un messaggio al canale Telegram. Usa la modalità markdown per
    formattare il messaggio.
    """
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN_V2)
        logger.info("Messaggio inviato con successo!")
    except Exception as e:
        logger.error(f"Errore durante l'invio del messaggio: {e}")

@app.route("/")
def home():
    return "🤖 Bot attivo"

@app.route("/fetch_offer")
def fetch_offer():
    """
    Endpoint da pingare (ad es. ogni 60 minuti con UptimeRobot) per recuperare
    l'offerta migliore non ancora inviata e spedirla su Telegram.
    """
    offer = get_best_offer()
    if offer is None:
        logger.info("Nessuna nuova offerta trovata.")
        return "Nessuna nuova offerta trovata."

    title = offer.get("title", "N/A")
    link = offer.get("link", "N/A")
    description = offer.get("description", "")

    # Prepara il messaggio in formato Markdown
    message = f"🔥 *{title}*\n\n{description}\n\n🔗 [Acquista ora]({link})"

    # Invia il messaggio su Telegram
    asyncio.run(send_telegram_message(message))

    # Registra l'offerta come inviata per evitare duplicati
    sent_offers = load_sent_offers()
    offer_id = offer.get("id", link)
    sent_offers.append(offer_id)
    save_sent_offers(sent_offers)

    logger.info(f"Offerta inviata: {title}")
    return "Offerta inviata!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

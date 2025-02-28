import requests
import hashlib
import hmac
import base64
import time
import urllib.parse
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode
from bs4 import BeautifulSoup
import os
import logging

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione Amazon PA‑API
AWS_ACCESS_KEY = "AKPAV0YTNY1740423739"
AWS_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2h"
ASSOCIATE_TAG = "new1707-21"

# Configurazione Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
TELEGRAM_CHAT_ID = "-1002290458283"

# Crea l'app Flask e il bot Telegram
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def generate_amazon_signed_url():
    """
    Genera una URL firmata per effettuare una richiesta ItemSearch alla PA‑API.
    """
    endpoint = "webservices.amazon.it"
    uri = "/onca/xml"
    params = {
        "Service": "AWSECommerceService",
        "Operation": "ItemSearch",
        "AWSAccessKeyId": AWS_ACCESS_KEY,
        "AssociateTag": ASSOCIATE_TAG,
        "SearchIndex": "All",
        "ResponseGroup": "ItemAttributes,Offers",
        "Keywords": "offerte",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    sorted_params = sorted(params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    string_to_sign = f"GET\n{endpoint}\n{uri}\n{query_string}"
    signature = hmac.new(AWS_SECRET_KEY.encode('utf-8'),
                         string_to_sign.encode('utf-8'),
                         hashlib.sha256).digest()
    signature = base64.b64encode(signature).decode()
    signed_url = f"https://{endpoint}{uri}?{query_string}&Signature={urllib.parse.quote(signature)}"
    logger.info(f"Generated Signed URL: {signed_url}")
    return signed_url

def get_amazon_offers():
    """
    Effettua una richiesta alla PA‑API e restituisce un testo con le offerte trovate.
    """
    url = generate_amazon_signed_url()
    response = requests.get(url)
    logger.info(f"Amazon API Response: {response.content}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("Item")
        if not items:
            return "Nessuna offerta trovata."
        offers_text = ""
        for item in items[:5]:
            title_tag = item.find("Title")
            price_tag = item.find("FormattedPrice")
            detail_url_tag = item.find("DetailPageURL")
            if title_tag and price_tag and detail_url_tag:
                title = title_tag.get_text().strip()
                price = price_tag.get_text().strip()
                detail_url = detail_url_tag.get_text().strip()
                offers_text += f"🔥 *{title}*\n💰 *{price}*\n🔗 [Acquista ora]({detail_url})\n\n"
        return offers_text if offers_text else "Nessuna offerta trovata."
    else:
        logger.error(f"Errore nella richiesta: {response.status_code}")
        return f"Errore nella richiesta: {response.status_code}"

def send_telegram_message(message):
    """
    Invia un messaggio al canale o gruppo Telegram configurato.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN_V2)
        logger.info("Messaggio inviato con successo!")
    except Exception as e:
        logger.error(f"Errore durante l'invio del messaggio: {e}")

@app.route("/")
def home():
    return "🤖 Bot attivo"

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/fetch_offers")
def fetch_offers():
    offers = get_amazon_offers()
    logger.info(f"Offerte trovate: {offers}")
    send_telegram_message(offers)
    return "Offerte inviate!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

import requests
import json
import logging
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode
from aws_requests_auth.aws_auth import AWSRequestsAuth
import asyncio

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

def generate_amazon_paapi5_request():
    """
    Genera il corpo della richiesta per la PA-API 5.0.
    """
    params = {
        "Keywords": "offerte",
        "SearchIndex": "All",
        "ItemCount": 5,
        "Resources": ["ItemInfo.Title", "Offers.Listings.Price"],
        "PartnerTag": ASSOCIATE_TAG,
        "PartnerType": "Associates"
    }
    return json.dumps(params)

def get_amazon_offers():
    """
    Effettua una richiesta alla PA-API 5.0 e restituisce un testo con le offerte trovate.
    """
    endpoint = "webservices.amazon.eu"
    url = f"https://{endpoint}/paapi5/searchitems"
    params = generate_amazon_paapi5_request()
    auth = AWSRequestsAuth(
        aws_access_key=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_host=endpoint,
        aws_region="eu-west-1",
        aws_service="ProductAdvertisingAPI"
    )
    headers = {
        "Content-Type": "application/json",
        "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
    }
    response = requests.post(url, data=params, headers=headers, auth=auth)
    if response.status_code == 200:
        return parse_amazon_response(response.json())
    else:
        logger.error(f"Errore nella richiesta: {response.status_code}")
        return f"Errore nella richiesta: {response.status_code}"

def parse_amazon_response(response):
    """
    Parsa la risposta della PA-API 5.0 e restituisce un testo formattato.
    """
    items = response.get("SearchResult", {}).get("Items", [])
    if not items:
        return "Nessuna offerta trovata."
    offers_text = ""
    for item in items[:5]:
        title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", "N/A")
        price = item.get("Offers", {}).get("Listings", [{}])[0].get("Price", {}).get("DisplayAmount", "N/A")
        detail_url = item.get("DetailPageURL", "N/A")
        offers_text += f"🔥 *{title}*\n💰 *{price}*\n🔗 [Acquista ora]({detail_url})\n\n"
    return offers_text if offers_text else "Nessuna offerta trovata."

async def send_telegram_message(message):
    """
    Invia un messaggio al canale o gruppo Telegram configurato.
    """
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN_V2)
        logger.info("Messaggio inviato con successo!")
    except Exception as e:
        logger.error(f"Errore durante l'invio del messaggio: {e}")

@app.route("/")
def home():
    return "🤖 Bot attivo"

@app.route("/fetch_offers")
def fetch_offers():
    offers = get_amazon_offers()
    logger.info(f"Offerte trovate: {offers}")
    asyncio.run(send_telegram_message(offers))
    return "Offerte inviate!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

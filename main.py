import time
import random
import threading
import schedule
import os
import asyncio
from telegram import Bot
from flask import Flask
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import requests
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException

# Configurazione
TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"  # Token del bot Telegram
CHAT_ID = "-1002290458283"  # ID della chat Telegram
AMAZON_ASSOCIATE_TAG = "new1707-21"  # Tag di affiliazione Amazon
AMAZON_ACCESS_KEY = "AKPAV0YTNY1740423739"  # Access Key di PA-API
AMAZON_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2h"  # Secret Key di PA-API
AMAZON_HOST = "webservices.amazon.it"  # Endpoint PA-API per l'Italia
AMAZON_REGION = "eu-west-1"  # Regione PA-API

SENT_ASINS_FILE = "sent_asins.txt"  # File per memorizzare gli ASIN già inviati
PULSE_URL = "https://telegram-amazon-bot-9zsc.onrender.com/ping"  # URL per il keep-alive

# Inizializzazione del client PA-API
api = DefaultApi(
    access_key=AMAZON_ACCESS_KEY,
    secret_key=AMAZON_SECRET_KEY,
    host=AMAZON_HOST,
    region=AMAZON_REGION
)

# Funzioni di gestione ASIN
def load_sent_asins():
    """Carica gli ASIN già inviati da un file."""
    if os.path.exists(SENT_ASINS_FILE):
        with open(SENT_ASINS_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

sent_asins = load_sent_asins()

def save_sent_asins():
    """Salva gli ASIN già inviati in un file."""
    with open(SENT_ASINS_FILE, "w") as file:
        file.write("\n".join(sent_asins))

def add_affiliate_tag(url):
    """Aggiunge il tag di affiliazione a un URL di Amazon."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['tag'] = AMAZON_ASSOCIATE_TAG
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))

def get_amazon_offers():
    """Recupera le offerte da Amazon utilizzando PA-API."""
    print("🔍 Avvio ricerca offerte con PA-API...")
    offers = []
    seen_products = set()

    try:
        # Configura la richiesta di ricerca
        search_request = SearchItemsRequest(
            partner_tag=AMAZON_ASSOCIATE_TAG,
            partner_type="Associates",
            keywords="offerta",  # Parola chiave per la ricerca
            resources=[
                SearchItemsResource.ITEMINFO_TITLE,
                SearchItemsResource.OFFERS_LISTINGS_PRICE,
                SearchItemsResource.IMAGES_PRIMARY_MEDIUM,
                SearchItemsResource.DETAIL_PAGE_URL
            ],
            item_count=10  # Numero massimo di risultati
        )

        # Esegui la richiesta
        response = api.search_items(search_request)

        # Elabora i risultati
        for item in response.search_result.items:
            asin = item.asin
            if asin in seen_products or asin in sent_asins:
                continue
            seen_products.add(asin)

            title = item.item_info.title.display_value
            url = item.detail_page_url
            full_url = add_affiliate_tag(url)

            offers.append({'title': title, 'link': full_url, 'asin': asin})

    except ApiException as e:
        print(f"⚠️ Errore PA-API: {e}")

    return offers

async def send_telegram(offer):
    """Invia un'offerta tramite Telegram."""
    try:
        bot = Bot(token=TOKEN)
        text = (f"🔥 **{offer['title']}**\n\n"
                f"🎉 **Super Offerta!**\n\n"
                f"🔗 [Acquista ora]({offer['link']})")
        await asyncio.sleep(random.uniform(5, 15))  # Ritardo per evitare blocco
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown", disable_web_page_preview=False)
        sent_asins.add(offer['asin'])
        save_sent_asins()
        print(f"✅ Invio completato: {offer['title'][:30]}...")
    except Exception as e:
        print(f"❌ Errore invio Telegram: {str(e)}")

async def job():
    """Esegue il lavoro principale: cerca offerte e invia un messaggio."""
    print("⚡ Avvio nuovo scan")
    offers = get_amazon_offers()
    if offers:
        random.shuffle(offers)
        for offer in offers:
            if offer['asin'] not in sent_asins:
                await send_telegram(offer)
                break
    else:
        print("⏭️ Nessuna offerta trovata")

def keep_alive():
    """Mantiene attivo il bot effettuando richieste periodiche."""
    while True:
        try:
            time.sleep(600)
            response = requests.get(PULSE_URL, timeout=10)
            print(f"🌍 Ping a Render: {response.status_code}")
        except requests.RequestException as e:
            print(f"⚠️ Errore keep_alive: {e}")

def run_scheduler():
    """Avvia lo scheduler per eseguire il job periodicamente."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    schedule.every(35).to(55).minutes.do(lambda: loop.run_until_complete(job()))
    while True:
        schedule.run_pending()
        time.sleep(60)

# Configurazione Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot attivo"

@app.route('/ping')
def ping():
    return "Bot is running!", 200

if __name__ == "__main__":
    # Avvia lo scheduler e il keep-alive in thread separati
    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    # Avvia l'app Flask
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)), use_reloader=False)

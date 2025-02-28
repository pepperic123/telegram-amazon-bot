import time
import random
import threading
import schedule
import os
import asyncio
import json
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from telegram import Bot
from flask import Flask
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import requests

# Configurazione
TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1002290458283"
AMAZON_ASSOCIATE_TAG = "new1707-21"
AWS_ACCESS_KEY = "nascosto"  # Inserisci la tua Access Key
AWS_SECRET_KEY = "nascosto"  # Inserisci la tua Secret Key

SENT_ASINS_FILE = "sent_asins.txt"
PULSE_URL = "https://telegram-amazon-bot-9zsc.onrender.com/ping"  # Modifica con il tuo URL

# Inizializzazione del client PA-API
paapi5_client = boto3.client(
    'paapi5',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='eu-west-1'
)

# Funzioni di gestione ASIN
def load_sent_asins():
    if os.path.exists(SENT_ASINS_FILE):
        with open(SENT_ASINS_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

sent_asins = load_sent_asins()

def save_sent_asins():
    with open(SENT_ASINS_FILE, "w") as file:
        file.write("\n".join(sent_asins))

def add_affiliate_tag(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['tag'] = AMAZON_ASSOCIATE_TAG
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))

def get_amazon_offers():
    print("🔍 Avvio ricerca offerte con PA-API...")
    offers = []
    seen_products = set()

    try:
        # Esempio di ricerca di prodotti in offerta
        response = paapi5_client.search_items(
            PartnerTag=AMAZON_ASSOCIATE_TAG,
            PartnerType='Associates',
            Keywords='offerta',
            SearchIndex='All',
            Resources=['Images.Primary.Medium', 'ItemInfo.Title', 'Offers.Listings.Price']
        )

        for item in response['SearchResult']['Items']:
            asin = item['ASIN']
            if asin in seen_products or asin in sent_asins:
                continue
            seen_products.add(asin)

            title = item['ItemInfo']['Title']['DisplayValue']
            url = item['DetailPageURL']
            full_url = add_affiliate_tag(url)

            offers.append({'title': title, 'link': full_url, 'asin': asin})
            if len(offers) >= 10:
                break

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"⚠️ Errore credenziali: {str(e)}")
    except Exception as e:
        print(f"⚠️ Errore PA-API: {str(e)}")

    return offers

async def send_telegram(offer):
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
    while True:
        try:
            time.sleep(600)
            response = requests.get(PULSE_URL, timeout=10)
            print(f"🌍 Ping a Render: {response.status_code}")
        except requests.RequestException as e:
            print(f"⚠️ Errore keep_alive: {e}")

def run_scheduler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    schedule.every(35).to(55).minutes.do(lambda: loop.run_until_complete(job()))
    while True:
        schedule.run_pending()
        time.sleep(60)

app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Bot attivo"
@app.route('/ping')
def ping():
    return "Bot is running!", 200

if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)), use_reloader=False)

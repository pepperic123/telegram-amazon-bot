import time
import random
import asyncio
import schedule
import threading
from telegram import Bot
from flask import Flask
from config import (
    AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, AMAZON_CATEGORIES
)
from amazon_api_wrapper import AmazonApiWrapper
import requests

# Inizializza l'API Amazon
amazon_api = AmazonApiWrapper()

# Memorizza gli ASIN inviati per evitare duplicati
GITHUB_REPO = "https://raw.githubusercontent.com/pepperic123/telegram-amazon-bot/main/sent_asins.txt"
GITHUB_UPDATE_URL = "https://api.github.com/repos/pepperic123/telegram-amazon-bot/contents/sent_asins.txt"
GITHUB_TOKEN = "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"

def load_sent_asins():
    try:
        response = requests.get(GITHUB_REPO, timeout=5)
        if response.status_code == 200:
            return set(response.text.splitlines())
    except requests.RequestException:
        pass
    return set()

sent_asins = load_sent_asins()

def update_sent_asins():
    try:
        # Aggiorna il file su GitHub con gli ASIN inviati
        content = "\n".join(sent_asins)
        payload = {
            "message": "Aggiornamento lista ASIN inviati",
            "content": content,
            "sha": "latest_sha_here",  # Devi ottenere l'ultimo sha del file
        }
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
        }
        response = requests.put(GITHUB_UPDATE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ Lista ASIN aggiornata su GitHub")
        else:
            print(f"❌ Errore aggiornamento su GitHub: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore nell'aggiornamento di GitHub: {str(e)}")

# Funzione per inviare un'offerta su Telegram
async def send_telegram(offer):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        text = (
            f"🔥 **{offer['title']}**\n\n💰 **Prezzo:** {offer['price']}\n\n"
            f"🔗 [Compra ora]({offer['link']})"
        )
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=offer['image'], caption=text, parse_mode="Markdown")
        sent_asins.add(offer['asin'])
        print(f"✅ Offerta inviata: {offer['title'][:30]}...")
    except Exception as e:
        print(f"❌ Errore invio Telegram: {str(e)}")

# Funzione principale per trovare e inviare offerte
def job():
    print("⚡ Avvio ricerca offerte")
    category = random.choice(AMAZON_CATEGORIES)
    offers = amazon_api.get_offers(category)

    if offers:
        random.shuffle(offers)
        for offer in offers:
            if offer['asin'] not in sent_asins:
                asyncio.run(send_telegram(offer))
                break
    else:
        print("⏭️ Nessuna offerta trovata")

    # Aggiorna la lista degli ASIN inviati su GitHub
    update_sent_asins()

# Pianificazione dell'invio automatico delle offerte
def run_scheduler():
    schedule.every(29).to(55).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Creazione di un server Flask (utile per Render/UptimeRobot)
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot attivo e funzionante!"

if __name__ == "__main__":
    print("🚀 Avvio del bot e del web server...")
    threading.Thread(target=run_scheduler, daemon=True).start()

    # Avvio immediato della prima offerta
    job()

    app.run(host="0.0.0.0", port=8000)  # Flask come servizio principale

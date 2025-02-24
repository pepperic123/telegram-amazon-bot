import requests
import json
import schedule
import time
from telegram import Bot
from config import TOKEN, CHAT_ID, RAPIDAPI_KEY

# 🔹 Inizializza il bot di Telegram
bot = Bot(token=TOKEN)

# 🔹 Funzione per ottenere offerte da Amazon via RapidAPI
def get_amazon_offers(keyword="laptop"):
    url = "https://real-time-amazon-data.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    params = {
        "q": keyword,
        "country": "IT"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print("📢 Offerte trovate:", data.get("data", []))  # Debug
        return data.get("data", [])
    else:
        print("❌ Errore API Amazon:", response.text)
        return []

# 🔹 Funzione per inviare un'offerta su Telegram
def send_offer_to_telegram(offer):
    try:
        title = offer.get("title", "Offerta Amazon")
        price = offer.get("price", "N/A")
        url = offer.get("url", "")
        image = offer.get("image", "")

        message = f"🔥 {title}\n💰 Prezzo: {price}\n🔗 {url}"
        print("📢 Inviando messaggio:", message)  # Debug

        bot.send_photo(chat_id=CHAT_ID, photo=image, caption=message)
        print("✅ Offerta inviata con successo!")
    except Exception as e:
        print("❌ Errore nell'invio dell'offerta:", str(e))

# 🔹 Funzione principale per il bot
def job():
    print("🔍 Recupero nuove offerte...")
    offers = get_amazon_offers("laptop")  # Puoi cambiare la categoria
    if offers:
        send_offer_to_telegram(offers[0])  # Invia solo la prima offerta
    else:
        print("⚠️ Nessuna offerta trovata.")

# 🔹 Pianifica il bot per inviare offerte ogni ora
schedule.every(1).hours.do(job)

print("🤖 Bot avviato! In attesa della prossima offerta...")

while True:
    schedule.run_pending()
    time.sleep(60)  # Controlla ogni minuto

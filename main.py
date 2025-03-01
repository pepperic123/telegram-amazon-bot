import os
import time
import requests
import schedule
from python_amazon_paapi import AmazonAPI

# Configurazione delle credenziali Amazon
AMAZON_ACCESS_KEY = "AKPAV0YTNY1740423739"
AMAZON_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2h"
AMAZON_ASSOCIATE_TAG = "new1707-21"  # Il tuo codice di affiliazione

# Configura l'API di Amazon
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOCIATE_TAG, "IT")

# Configurazione di Telegram
TELEGRAM_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1002290458283"

# File per tenere traccia degli ASIN già inviati
SENT_ASINS_FILE = "sent_asins.txt"

def load_sent_asins():
    """Carica gli ASIN già inviati da un file."""
    if not os.path.exists(SENT_ASINS_FILE):
        return set()
    with open(SENT_ASINS_FILE, "r") as f:
        return set(f.read().splitlines())

def save_sent_asin(asin):
    """Salva un nuovo ASIN nel file."""
    with open(SENT_ASINS_FILE, "a") as f:
        f.write(asin + "\n")

def get_amazon_asins():
    """Simula il recupero di ASIN da Amazon (puoi sostituire questa logica con uno scraping reale)."""
    # Esempio di ASIN (sostituisci con la tua logica per ottenere ASIN reali)
    return ["B08N5WRWNW", "B09G3HRP7S"]

def get_product_info(asin):
    """Recupera le informazioni del prodotto utilizzando l'API di Amazon."""
    try:
        product = amazon.get_items(asin)
        if product and product.items:
            item = product.items[0]
            title = item.item_info.title.display_value if item.item_info.title else "Offerta Amazon"
            price = item.offers.listings[0].price.display_amount if item.offers else "N/A"
            image = item.images.primary.large.url if item.images and item.images.primary else None
            link = f"https://www.amazon.it/dp/{asin}?tag={AMAZON_ASSOCIATE_TAG}"
            return title, price, image, link
    except Exception as e:
        print(f"Errore nel recupero prodotto {asin}: {e}")
    return None, None, None, None

def send_to_telegram(title, price, image, link):
    """Invia un messaggio con l'offerta a Telegram."""
    message = f"\U0001F525 *Super Offerta!* \U0001F525\n\n{title}\n\n\U0001F4B0 *Prezzo:* {price}\n\n\U0001F517 [Acquista ora]({link})"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload)
    
    if image:
        img_payload = {
            "chat_id": CHAT_ID,
            "photo": image,
            "caption": message,
            "parse_mode": "Markdown"
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=img_payload)

def send_offers():
    """Invia le offerte a Telegram."""
    sent_asins = load_sent_asins()
    asins = get_amazon_asins()
    
    for asin in asins:
        if asin not in sent_asins:
            title, price, image, link = get_product_info(asin)
            if title and link:
                send_to_telegram(title, price, image, link)
                save_sent_asin(asin)
            time.sleep(5)  # Evita sovraccarico API

# Pianifica l'invio ogni 30 minuti
schedule.every(30).minutes.do(send_offers)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)

import os
import time
import requests
import schedule
from python_amazon_paapi import AmazonAPI  # Corretto l'import

# Imposta le tue credenziali
TELEGRAM_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1001434969904"
AMAZON_ACCESS_KEY = "AKPAV0YTNY1740423739"
AMAZON_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2hY"
AMAZON_ASSOCIATE_TAG = "new1707-21"

# Configura l'API di Amazon
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOCIATE_TAG, "IT")

# Recupera gli ASIN direttamente da Amazon
def get_asins_from_amazon():
    try:
        search_result = amazon.search_items(keywords="offerte", search_index="All", item_count=10)
        if search_result and search_result.items:
            return [item.asin for item in search_result.items if item.asin]
    except Exception as e:
        print(f"Errore nel recupero degli ASIN: {e}")
    return []

# Recupera gli ASIN già inviati
def get_sent_asins():
    if not os.path.exists("sent_asins.txt"):
        return set()
    with open("sent_asins.txt", "r") as f:
        return set(line.strip() for line in f.readlines())

# Salva gli ASIN inviati
def save_sent_asin(asin):
    with open("sent_asins.txt", "a") as f:
        f.write(asin + "\n")

# Recupera informazioni sui prodotti
def get_product_info(asin):
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

# Invia il messaggio su Telegram
def send_to_telegram(title, price, image, link):
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

# Processa e invia le offerte
def send_offers():
    asins = get_asins_from_amazon()
    sent_asins = get_sent_asins()
    
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

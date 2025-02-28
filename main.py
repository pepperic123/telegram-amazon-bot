import requests
from bs4 import BeautifulSoup
import telebot
import time
import os
import random

# Configurazione bot Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1001434969904"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Codice affiliato Amazon
AFFILIATE_TAG = "new1707-21"

# File per tracciare gli ASIN già inviati
SENT_ASINS_FILE = "sent_asins.txt"

def load_sent_asins():
    if os.path.exists(SENT_ASINS_FILE):
        with open(SENT_ASINS_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_sent_asin(asin):
    with open(SENT_ASINS_FILE, "a") as f:
        f.write(asin + "\n")

def get_amazon_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Errore {response.status_code} nel caricamento della pagina {url}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    title_tag = soup.find("span", id="productTitle")
    title = title_tag.text.strip() if title_tag else "Offerta Amazon"
    
    asin_tag = soup.find("input", {"id": "ASIN"})
    asin = asin_tag["value"] if asin_tag else str(random.randint(100000, 999999))
    
    image_tag = soup.find("img", id="landingImage")
    image_url = image_tag["src"] if image_tag else "https://via.placeholder.com/300"
    
    price_tag = soup.find("span", class_="a-price-whole")
    price = price_tag.text.strip() if price_tag else "N/A"
    
    return {"title": title, "image_url": image_url, "url": url, "asin": asin, "price": price}

def send_telegram_message(product):
    affiliate_url = f"{product['url']}?tag={AFFILIATE_TAG}"
    message = f"\U0001F525 *Super Offerta!* \U0001F525\n\n"
    message += f"{product['title']}\n"
    message += f"\n💰 Prezzo: {product['price']} €\n"
    message += f"🔗 [Acquista ora]({affiliate_url})\n"
    
    bot.send_photo(CHAT_ID, product["image_url"], caption=message, parse_mode="Markdown")
    print("Messaggio inviato su Telegram!")

def main():
    sent_asins = load_sent_asins()
    amazon_urls = [
        "https://www.amazon.it/gp/bestsellers",
        "https://www.amazon.it/gp/movers-and-shakers",
    ]
    
    for url in amazon_urls:
        product = get_amazon_product_details(url)
        if product and product["asin"] not in sent_asins:
            send_telegram_message(product)
            save_sent_asin(product["asin"])
        time.sleep(5)  # Pausa per evitare blocchi

while True:
    main()
    time.sleep(1800)  # Ripete ogni 30 minuti
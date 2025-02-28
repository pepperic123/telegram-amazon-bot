import requests
from bs4 import BeautifulSoup
import telebot
import time
import random
import os

# Configurazione bot Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1001434969904"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# URL delle offerte Amazon
AMAZON_URLS = [
    "https://www.amazon.it/gp/bestsellers",
    "https://www.amazon.it/gp/movers-and-shakers",
]

# Percorso file per evitare ripetizioni
SENT_ASINS_FILE = "sent_asins.txt"

def load_sent_asins():
    if os.path.exists(SENT_ASINS_FILE):
        with open(SENT_ASINS_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_sent_asin(asin):
    with open(SENT_ASINS_FILE, "a") as f:
        f.write(asin + "\n")

# Funzione per estrarre informazioni dal prodotto Amazon
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
    
    # Estrazione titolo
    title_tag = soup.find("span", id="productTitle")
    title = title_tag.text.strip() if title_tag else "Offerta Amazon"
    
    # Estrazione ASIN (per evitare duplicati)
    asin_tag = soup.find("input", {"id": "ASIN"})
    asin = asin_tag["value"] if asin_tag else str(random.randint(100000, 999999))
    
    # Estrazione immagine
    image_tag = soup.find("img", id="landingImage")
    image_url = image_tag["src"] if image_tag else "https://via.placeholder.com/300"
    
    return {"title": title, "image_url": image_url, "url": url, "asin": asin}

# Funzione per inviare il messaggio su Telegram
def send_telegram_message(product):
    affiliate_url = f"{product['url']}?tag=new1707-21"
    message = f"🔥 *Super Offerta!* 🔥\n\n"
    message += f"[{product['title']}]({affiliate_url})\n"
    message += f"🛒 *Clicca sull'immagine per vedere il prezzo!*\n"
    
    bot.send_photo(CHAT_ID, product["image_url"], caption=message, parse_mode="Markdown")
    print("Messaggio inviato su Telegram!")

# Avvio dello scraping
def main():
    sent_asins = load_sent_asins()
    
    for url in AMAZON_URLS:
        product = get_amazon_product_details(url)
        if product and product["asin"] not in sent_asins:
            send_telegram_message(product)
            save_sent_asin(product["asin"])
        time.sleep(5)  # Pausa per evitare blocchi

# Esecuzione periodica ogni 30 minuti
while True:
    main()
    time.sleep(1800)

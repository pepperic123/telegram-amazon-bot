import requests
from bs4 import BeautifulSoup
import telebot
import time

# Configurazione bot Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1001434969904"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# URL delle offerte Amazon
AMAZON_URLS = [
    "https://www.amazon.it/gp/bestsellers",  # Bestseller Amazon
    "https://www.amazon.it/gp/movers-and-shakers",  # Trend di crescita
]

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
    title = title_tag.text.strip() if title_tag else "Titolo non trovato"
    
    # Estrazione prezzo
    price_tag = soup.find("span", class_="a-price-whole")
    decimal_tag = soup.find("span", class_="a-price-fraction")
    price = price_tag.text.strip() if price_tag else "Prezzo non disponibile"
    decimal = decimal_tag.text.strip() if decimal_tag else "00"
    full_price = f"{price},{decimal}€" if price_tag else "Prezzo non disponibile"
    
    # Estrazione immagine
    image_tag = soup.find("img", id="landingImage")
    image_url = image_tag["src"] if image_tag else None
    
    return {"title": title, "price": full_price, "image_url": image_url, "url": url}

# Funzione per inviare il messaggio su Telegram
def send_telegram_message(product):
    if not product["image_url"]:
        print("⚠️ Nessuna immagine disponibile, invio solo testo.")
        message = f"🔥 *Super Offerta!* 🔥\n\n[{product['title']}]({product['url']})\n💰 *Prezzo:* {product['price']}€\n"
        bot.send_message(CHAT_ID, message, parse_mode="Markdown")
    else:
        message = f"🔥 *Super Offerta!* 🔥\n\n[{product['title']}]({product['url']})\n💰 *Prezzo:* {product['price']}€\n"
        bot.send_photo(CHAT_ID, product["image_url"], caption=message, parse_mode="Markdown")
    print("Messaggio inviato su Telegram!")

# Avvio dello scraping
def main():
    for url in AMAZON_URLS:
        product = get_amazon_product_details(url)
        if product:
            send_telegram_message(product)
        time.sleep(5)  # Pausa tra le richieste per evitare blocchi

if __name__ == "__main__":
    main()

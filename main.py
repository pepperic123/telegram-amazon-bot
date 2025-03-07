import time
import random
import requests
import asyncio
import schedule
import json
import threading
from bs4 import BeautifulSoup
from telegram import Bot
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from flask import Flask

# Configurazione
TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1002290458283"
AMAZON_ASSOCIATE_TAG = "new1707-21"
AMAZON_URLS = [
    "https://www.amazon.it/gp/most-gifted/",  # I più regalati
    "https://www.amazon.it/gp/most-wished-for/",  # I più desiderati
    "https://www.amazon.it/gp/bestsellers/appliances/",  # Bestseller in Elettrodomestici
    "https://www.amazon.it/gp/bestsellers/baby/",  # Bestseller in Prima infanzia
    "https://www.amazon.it/gp/bestsellers/books/",  # Bestseller in Libri
    "https://www.amazon.it/gp/bestsellers/diy/",  # Bestseller in Fai da te
    "https://www.amazon.it/gp/bestsellers/kitchen/",  # Bestseller in Cucina e accessori
    "https://www.amazon.it/gp/bestsellers/luggage/",  # Bestseller in Valigeria
    "https://www.amazon.it/gp/bestsellers/music/",  # Bestseller in CD e Vinili
    "https://www.amazon.it/gp/bestsellers/pets/",  # Bestseller in Prodotti per animali domestici
    "https://www.amazon.it/gp/bestsellers/shoes/",  # Bestseller in Scarpe e borse
    "https://www.amazon.it/gp/bestsellers/watches/",  # Bestseller in Orologi
    "https://www.amazon.it/gp/holiday-deals/",  # Offerte speciali per festività e Black Friday
    "https://www.amazon.it/gp/warehouse-deals/",  # Offerte Amazon Warehouse (prodotti usati e ricondizionati)
    "https://www.amazon.it/gp/deals/",  # Offerte generali
    "https://www.amazon.it/gp/bestsellers/electronics/",  # Bestseller in Elettronica
    "https://www.amazon.it/gp/bestsellers/computers/",  # Bestseller in Informatica
    "https://www.amazon.it/gp/bestsellers/home/",  # Bestseller in Casa e Cucina
    "https://www.amazon.it/gp/bestsellers/sports/",  # Bestseller in Sport e Tempo Libero
    "https://www.amazon.it/gp/bestsellers/fashion/",  # Bestseller in Abbigliamento e Moda
    "https://www.amazon.it/gp/bestsellers/toys/",  # Bestseller in Giochi e Giocattoli
    "https://www.amazon.it/gp/bestsellers/videogames/",  # Bestseller in Videogiochi
    "https://www.amazon.it/gp/bestsellers/beauty/",  # Bestseller in Bellezza e Cura della Persona
    "https://www.amazon.it/gp/bestsellers/automotive/",  # Bestseller in Auto e Moto
    "https://www.amazon.it/gp/bestsellers/grocery/",  # Bestseller in Alimentari e Cura della Casa
    "https://www.amazon.it/gp/bestsellers/",
    "https://www.amazon.it/gp/movers-and-shakers/",
    "https://www.amazon.it/gp/new-releases/",
    "https://www.amazon.it/b/?node=77925031/",
    "https://www.amazon.it/b/?node=12684621031",
    "https://www.amazon.it/gp/browse.html?node=83450031",
    "https://www.amazon.it/gp/browse.html?node=524013031"
]

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"
]

# Caricare ASIN inviati da GitHub
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

def add_affiliate_tag(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['tag'] = AMAZON_ASSOCIATE_TAG
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))

def get_amazon_offers():
    print("🔍 Avvio scraping...")
    offers = []
    seen_products = set()
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for url in AMAZON_URLS:
        print(f"📡 Scraping {url}")
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select("div.p13n-sc-uncoverable-faceout")

            for item in items:
                link = item.find('a', {'class': 'a-link-normal'})
                if not link or "/dp/" not in link.get('href'):
                    continue
                
                asin = link.get("href").split("/dp/")[1].split("/")[0]
                if asin in seen_products or asin in sent_asins:
                    continue
                
                seen_products.add(asin)
                full_url = add_affiliate_tag(f"https://www.amazon.it{link.get('href').split('?')[0]}")
                app_link = f"https://www.amazon.it/dp/{asin}/?tag={AMAZON_ASSOCIATE_TAG}&app=amazon"
                title = item.select_one("span.a-size-base-plus, h2.a-size-mini, span.a-text-normal")
                title_text = title.get_text(strip=True) if title else "LE MIGLIORI OFFERTE DEL WEB"
                
                offers.append({'title': title_text, 'link': full_url, 'app_link': app_link, 'asin': asin})
                
                if len(offers) >= 10:
                    break
        except requests.RequestException:
            continue
    
    return offers

async def send_telegram(offer):
    try:
        bot = Bot(token=TOKEN)
        text = (f"🔥 **{offer['title']}**\n\n🎉 **Super Offerta!**\n\n"
                f"🔗 [Apri nell'app Amazon]({offer['app_link']})\n"
                f"🔗 [Apri nel browser]({offer['link']})")
        
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown", disable_web_page_preview=False)
        sent_asins.add(offer['asin'])
        print(f"✅ Invio completato: {offer['title'][:30]}...")
    except Exception as e:
        print(f"❌ Errore invio Telegram: {str(e)}")

def job():
    print("⚡ Avvio nuovo scan")
    offers = get_amazon_offers()
    if offers:
        random.shuffle(offers)
        for offer in offers:
            if offer['asin'] not in sent_asins:
                asyncio.run(send_telegram(offer))
                break
    else:
        print("⏭️ Nessuna offerta trovata")

def run_scheduler():
    schedule.every(29).to(55).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot attivo e funzionante!"

if __name__ == "__main__":
    print("🚀 Avvio del bot e del web server...")
    threading.Thread(target=run_scheduler, daemon=True).start()  # Avvia il bot in background

    # FORZA L'ESECUZIONE IMMEDIATA
    job()

    app.run(host="0.0.0.0", port=8000)  # Flask come servizio principale

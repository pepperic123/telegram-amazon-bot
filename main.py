import time
import random
import threading
import schedule
import os
import asyncio
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import Bot
from flask import Flask
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Configurazione
TOKEN = "7213198162:AA..."
CHAT_ID = "-1001434969904"
AMAZON_ASSOCIATE_TAG = "new1707-21"
AMAZON_URLS = [
    "https://www.amazon.it/gp/bestsellers/",
    "https://www.amazon.it/gp/movers-and-shakers/",
    "https://www.amazon.it/gp/new-releases/",
    "https://www.amazon.it/gp/most-wished-for/"
]

SENT_ASINS_FILE = "sent_asins.txt"
MAX_ASINS = 200  # Numero massimo di ASIN da salvare

# Configurazione Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

# User-Agent rotation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"
]
chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

# Caricare ASIN inviati
sent_asins = set()
def load_sent_asins():
    global sent_asins
    if os.path.exists(SENT_ASINS_FILE):
        with open(SENT_ASINS_FILE, "r") as file:
            sent_asins = set(file.read().splitlines())
load_sent_asins()

def save_sent_asins():
    global sent_asins
    sent_asins = set(list(sent_asins)[-MAX_ASINS:])  # Mantiene solo gli ultimi 200
    with open(SENT_ASINS_FILE, "w") as file:
        file.write("\n".join(sent_asins))

def add_affiliate_tag(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['tag'] = AMAZON_ASSOCIATE_TAG
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))

def extract_title(item):
    selectors = ['span.a-size-base-plus', 'h2.a-size-mini', 'span.a-text-normal']
    for selector in selectors:
        title_element = item.select_one(selector)
        if title_element and title_element.get_text(strip=True):
            return title_element.get_text(strip=True)
    return "LE MIGLIORI OFFERTE DEL WEB"

def get_amazon_offers():
    print("🔍 Avvio scraping...")
    driver = webdriver.Chrome(options=chrome_options)
    offers = []
    seen_products = set()
    
    for url in AMAZON_URLS:
        print(f"📡 Scraping {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 6))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        items = soup.select("div.p13n-sc-uncoverable-faceout")

        for item in items:
            try:
                link = item.find('a', {'class': 'a-link-normal'})
                if not link or "/dp/" not in link.get('href'):
                    continue
                
                asin = link.get("href").split("/dp/")[1].split("/")[0]
                if asin in seen_products or asin in sent_asins:
                    continue  # Salta prodotti già visti o inviati
                seen_products.add(asin)
                
                full_url = add_affiliate_tag(f"https://www.amazon.it{link.get('href').split('?')[0]}")
                title = extract_title(item)
                offers.append({'title': title, 'link': full_url, 'asin': asin})
                
                if len(offers) >= 10:
                    break
            except Exception as e:
                print(f"⚠️ Errore: {str(e)}")
                continue
    
    driver.quit()
    return offers

async def send_telegram(offer):
    try:
        bot = Bot(token=TOKEN)
        text = (f"🔥 **{offer['title']}**\n\n"
                f"🎉 **Super Offerta!**\n\n"
                f"🔗 [Acquista ora]({offer['link']})")
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown", disable_web_page_preview=False)
        sent_asins.add(offer['asin'])
        save_sent_asins()
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
    schedule.every(50).to(60).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)

app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Bot attivo"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    job()
    while True:
        time.sleep(3600)

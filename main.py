import time
import random
import threading
import os
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Bot
from flask import Flask
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from apscheduler.schedulers.background import BackgroundScheduler

# Configurazione
TOKEN = os.getenv("TELEGRAM_TOKEN", "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0")
CHAT_ID = os.getenv("CHAT_ID", "-1001434969904")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "new1707-21")
AMAZON_URLS = [
    "https://www.amazon.it/gp/bestsellers/",
    "https://www.amazon.it/gp/movers-and-shakers/",
    "https://www.amazon.it/gp/new-releases/",
    "https://www.amazon.it/gp/most-wished-for/"
]

# File per salvare gli ASIN già inviati
SENT_ASINS_FILE = "sent_asins.txt"

# Configurazione Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# User-Agent rotation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"
]
chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

# Caricare ASIN inviati da file
def load_sent_asins():
    if os.path.exists(SENT_ASINS_FILE):
        with open(SENT_ASINS_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

# Salvare ASIN inviati
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

def extract_title(item):
    selectors = ['span.a-size-base-plus', 'h2.a-size-mini', 'span.a-text-normal']
    for selector in selectors:
        title_element = item.select_one(selector)
        if title_element and title_element.get_text(strip=True):
            return title_element.get_text(strip=True)
    return "LE MIGLIORI OFFERTE DEL WEB"

def get_amazon_offers():
    print("🔍 Avvio scraping...")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
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

                full_url = add_affiliate_tag(f"https://www.amazon.it{link.get('href').split('?')[0]}")
                asin = link.get("href").split("/dp/")[1].split("/")[0]

                if asin in seen_products or asin in sent_asins:
                    continue
                seen_products.add(asin)

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

# Scheduler con APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(job, 'interval', minutes=random.randint(35, 55))
scheduler.start()

# Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Bot attivo"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    job()
    while True:
        time.sleep(3600)

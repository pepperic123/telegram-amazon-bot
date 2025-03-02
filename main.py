import time
import random
import threading
import schedule
import os
import asyncio
import json
import base64
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Bot
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import traceback

# Configurazione
TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1002290458283"
AMAZON_ASSOCIATE_TAG = "new1707-21"
AMAZON_URLS = [
    "https://www.amazon.it/gp/goldbox",
    "https://www.amazon.it/gp/bestsellers/",
    "https://www.amazon.it/gp/movers-and-shakers/",
    "https://www.amazon.it/gp/new-releases/",
    "https://www.amazon.it/gp/most-wished-for/",
    "https://www.amazon.it/b/?node=77925031/",
    "https://www.amazon.it/b/?node=12684621031",
    "https://www.amazon.it/gp/browse.html?node=83450031",
    "https://www.amazon.it/gp/browse.html?node=524013031",
    "https://www.amazon.it/gp/bestsellers/"
]

# Configurazione GitHub
GITHUB_TOKEN = "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"
GITHUB_REPO = "pepperic123/telegram-amazon-bot"
GITHUB_FILE_PATH = "sent_asins.txt"
GITHUB_API_URL = f"https://api.github.com/repos/pepperic123/telegram-amazon-bot/contents/sent_asins.txt"

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

# Caricare ASIN da GitHub
def load_sent_asins():
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(GITHUB_API_URL, headers=headers)

        if response.status_code == 200:
            file_data = response.json()
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            return set(content.splitlines()), file_data["sha"]
        else:
            print("⚠️ Nessun file trovato su GitHub, creandone uno nuovo...")
            return set(), None
    except Exception as e:
        print(f"❌ Errore nel caricamento da GitHub: {e}")
        traceback.print_exc()
        return set(), None

# Salvare ASIN su GitHub
def save_sent_asins():
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        content = "\n".join(sent_asins)
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        data = {
            "message": "Aggiornato sent_asins.txt",
            "content": encoded_content,
            "sha": github_file_sha
        }

        response = requests.put(GITHUB_API_URL, headers=headers, data=json.dumps(data))

        if response.status_code == 200 or response.status_code == 201:
            print("✅ ASIN aggiornati con successo su GitHub!")
        else:
            print(f"❌ Errore aggiornamento GitHub: {response.json()}")
    except Exception as e:
        print(f"❌ Errore nel salvataggio su GitHub: {e}")
        traceback.print_exc()

# Caricare gli ASIN salvati
sent_asins, github_file_sha = load_sent_asins()

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
                traceback.print_exc()
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
        traceback.print_exc()

def job():
    print("⚡ Avvio nuovo scan")
    offers = get_amazon_offers()
    print(f"🔍 Offerte trovate: {len(offers)}")
    if offers:
        random.shuffle(offers)
        for offer in offers:
            if offer['asin'] not in sent_asins:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_telegram(offer))
                loop.close()
                break
    else:
        print("⏭️ Nessuna offerta trovata")

def run_scheduler():
    print("⏰ Scheduler avviato")
    schedule.every(45).to(55).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Avvia lo scheduler in un thread separato
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Esegui il job immediatamente
    job()

    # Mantieni il programma in esecuzione
    while True:
        time.sleep(3600)
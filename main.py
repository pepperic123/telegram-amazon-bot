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
    "https://www.amazon.it/gp/bestsellers/",
    "https://www.amazon.it/gp/movers-and-shakers/",
    "https://www.amazon.it/gp/new-releases/",
    "https://www.amazon.it/b/?node=77925031/",
    "https://www.amazon.it/b/?node=12684621031",
    "https://www.amazon.it/gp/browse.html?node=83450031",
    "https://www.amazon.it/gp/browse.html?node=524013031"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"
]

GITHUB_REPO = "https://raw.githubusercontent.com/pepperic123/telegram-amazon-bot/main/sent_asins.txt"
GITHUB_UPDATE_URL = "https://api.github.com/repos/pepperic123/telegram-amazon-bot/contents/sent_asins.txt"
GITHUB_TOKEN = "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"

# Carica gli ASIN inviati
def load_sent_asins():
    try:
        response = requests.get(GITHUB_REPO, timeout=5)
        if response.status_code == 200:
            return set(response.text.splitlines())
    except requests.RequestException:
        pass
    return set()

sent_asins = load_sent_asins()

def save_sent_asins():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    sha = requests.get(GITHUB_UPDATE_URL, headers=headers).json().get("sha")
    content = "\n".join(sent_asins).encode("utf-8").decode("latin-1")
    data = json.dumps({"message": "Aggiornamento ASIN", "content": content.encode("utf-8").hex(), "sha": sha})
    requests.put(GITHUB_UPDATE_URL, headers=headers, data=data)

def add_affiliate_tag(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['tag'] = AMAZON_ASSOCIATE_TAG
    new_query = urlencode(query_params, doseq=True)
    normal_url = urlunparse(parsed_url._replace(query=new_query))
    deep_link = normal_url.replace("https://www.", "amazon://www.")
    return normal_url, deep_link

def extract_title(item):
    title_element = item.select_one("span.a-size-base-plus, h2.a-size-mini, span.a-text-normal")
    return title_element.get_text(strip=True) if title_element else "LE MIGLIORI OFFERTE DEL WEB"

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
                full_url, deep_link = add_affiliate_tag(f"https://www.amazon.it{link.get('href').split('?')[0]}")
                title = extract_title(item)
                offers.append({'title': title, 'link': full_url, 'deep_link': deep_link, 'asin': asin})
                
                if len(offers) >= 10:
                    break
        except requests.RequestException:
            continue
    
    return offers

async def send_telegram(offer):
    try:
        bot = Bot(token=TOKEN)
        text = (f"🔥 **{offer['title']}**\n\n🎉 **Super Offerta!**\n\n"
                f"🔗 [Apri nell'app Amazon]({offer['deep_link']})\n"
                f"🔗 [Apri nel browser]({offer['link']})")
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
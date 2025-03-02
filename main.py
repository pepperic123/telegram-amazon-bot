import time
import random
import threading
import schedule
import asyncio
import json
import base64
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import Bot
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from webdriver_manager.chrome import ChromeDriverManager
import traceback

# Configurazioni
TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1002290458283"
AMAZON_ASSOCIATE_TAG = "new1707-21"
REQUEST_TIMEOUT = 10
MAX_OFFERS = 15

AMAZON_URLS = [
    "https://www.amazon.it/gp/goldbox",
    "https://www.amazon.it/gp/bestsellers/",
    "https://www.amazon.it/gp/movers-and-shakers/",
    "https://www.amazon.it/gp/new-releases/",
    "https://www.amazon.it/gp/most-wished-for/",
    "https://www.amazon.it/b/?node=77925031/",
    "https://www.amazon.it/b/?node=12684621031",
    "https://www.amazon.it/gp/browse.html?node=83450031",
    "https://www.amazon.it/gp/browse.html?node=524013031"
]

# Configurazione GitHub
GITHUB_TOKEN = "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"
GITHUB_REPO = "pepperic123/telegram-amazon-bot"
GITHUB_FILE = "sent_asins.txt"
GITHUB_API_URL = f"https://api.github.com/repos/pepperic123/telegram-amazon-bot/contents/sent_asins.txt"

# Configurazione Selenium
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Rotazione User-Agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15"
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    return webdriver.Chrome(
        executable_path=ChromeDriverManager().install(),
        options=chrome_options
    )

# Gestione ASIN
class ASINManager:
    def __init__(self):
        self.sent_asins, self.file_sha = self.load_asins()

    def load_asins(self):
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content']).decode('utf-8')
                return set(content.splitlines()), data['sha']
            return set(), None
        except Exception as e:
            print(f"❌ Errore caricamento ASIN: {str(e)}")
            return set(), None

    def save_asins(self):
        try:
            content = "\n".join(self.sent_asins)
            encoded = base64.b64encode(content.encode()).decode()
            
            data = {
                "message": "Aggiornamento ASIN",
                "content": encoded,
                "sha": self.file_sha
            }
            
            response = requests.put(
                GITHUB_API_URL,
                headers={
                    "Authorization": f"token {GITHUB_TOKEN}",
                    "Content-Type": "application/json"
                },
                data=json.dumps(data),
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code in (200, 201):
                print("✅ ASIN salvati su GitHub")
                self.file_sha = response.json().get('content', {}).get('sha')
            else:
                print(f"❌ Errore salvataggio: {response.text}")
        except Exception as e:
            print(f"❌ Errore salvataggio ASIN: {str(e)}")

# Core dello scraping
class AmazonScraper:
    def __init__(self, asin_manager):
        self.asin_manager = asin_manager

    @staticmethod
    def add_affiliate_tag(url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query['tag'] = [AMAZON_ASSOCIATE_TAG]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def scrape_offers(self):
        print("🕸️ Avvio scraping Amazon...")
        driver = setup_driver()
        offers = []
        
        try:
            for url in AMAZON_URLS:
                print(f"🌐 Accesso a {url}")
                driver.get(url)
                time.sleep(random.uniform(2, 4))
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                items = soup.select("div[data-asin]:has(a[href*='/dp/'])")
                
                for item in items[:MAX_OFFERS]:
                    try:
                        link = item.find('a', {'href': True})
                        asin = item['data-asin']
                        
                        if not asin or asin in self.asin_manager.sent_asins:
                            continue
                            
                        title = self.extract_title(item)
                        affiliate_link = self.add_affiliate_tag(
                            f"https://www.amazon.it/dp/{asin}"
                        )
                        
                        offers.append({
                            'title': title,
                            'link': affiliate_link,
                            'asin': asin
                        })
                    except Exception as e:
                        print(f"⚠️ Errore processo item: {str(e)}")
        
        finally:
            driver.quit()
        
        return offers

    @staticmethod
    def extract_title(item):
        selectors = [
            'span.a-size-base-plus',
            'h2.a-size-mini',
            'span.a-text-normal'
        ]
        return next(
            (elem.get_text(strip=True) for selector in selectors 
             if (elem := item.select_one(selector))),
            "OFFERTA SPECIALE 🚨"
        )

# Gestione Telegram
class TelegramBot:
    def __init__(self, asin_manager):
        self.bot = Bot(token=TOKEN)
        self.asin_manager = asin_manager

    async def send_offer(self, offer):
        try:
            text = (
                f"🔥 **{offer['title']}**\n\n"
                f"💸 **Prezzo Scontato!**\n\n"
                f"🛒 [Acquista Ora]({offer['link']})"
            )
            
            await self.bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            
            self.asin_manager.sent_asins.add(offer['asin'])
            self.asin_manager.save_asins()
            print(f"✅ Inviato: {offer['title'][:50]}...")
            
        except Exception as e:
            print(f"❌ Errore invio: {str(e)}")
            traceback.print_exc()

# Scheduler e Main
def job(scraper, bot):
    print("\n🔔 Nuovo ciclo di scanning")
    offers = scraper.scrape_offers()
    
    if offers:
        random.shuffle(offers)
        for offer in offers[:3]:  # Limita a 3 offerte per ciclo
            if offer['asin'] not in scraper.asin_manager.sent_asins:
                asyncio.run(bot.send_offer(offer))
                time.sleep(random.uniform(5, 10))
                break
    else:
        print("⏭️ Nessuna nuova offerta trovata")

def scheduler_loop():
    asin_manager = ASINManager()
    scraper = AmazonScraper(asin_manager)
    bot = TelegramBot(asin_manager)
    
    schedule.every(29).to(55).minutes.do(
        lambda: job(scraper, bot)
    )
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("🚀 Avvio Amazon Deal Bot")
    threading.Thread(target=scheduler_loop, daemon=True).start()
    
    # Mantiene il programma attivo
    while True:
        time.sleep(3600)

import time
import random
import boto3
import amazon-paapi
from botocore.exceptions import NoCredentialsError
from telegram import Bot
from flask import Flask
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Configurazione Amazon PA-API
AWS_ACCESS_KEY = "AKPAV0YTNY1740423739"
AWS_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2h"
ASSOCIATE_TAG = "new1707-21"

# Configurazione Telegram
TELEGRAM_BOT_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
TELEGRAM_CHAT_ID = "-1002290458283"

# Crea l'app Flask e il bot Telegram
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Configura la sessione boto3 per l'accesso alla PA-API di Amazon
client = boto3.client(
    "advertising",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="us-east-1",  # Imposta la regione corretta
)

def get_amazon_offers():
    """
    Usa le PA-API di Amazon per ottenere le offerte.
    """
    try:
        response = client.search_items(
            Keywords="offerte",  # Puoi cambiare le parole chiave per la ricerca
            SearchIndex="All",  # Puoi specificare altre categorie
            Resources=[
                "ItemInfo.Title",
                "Offers.Listings.Price",
                "DetailPageURL"
            ],
            PartnerTag=ASSOCIATE_TAG,
            PartnerType="Associates",
        )

        items = response["Items"]
        if not items:
            return "Nessuna offerta trovata."

        offers_text = ""
        for item in items[:5]:  # Mostra i primi 5 risultati
            title = item["ItemInfo"]["Title"]["DisplayValue"]
            price = item["Offers"]["Listings"][0]["Price"]["DisplayAmount"]
            detail_url = item["DetailPageURL"]
            offers_text += f"🔥 *{title}*\n💰 *{price}*\n🔗 [Acquista ora]({detail_url})\n\n"

        return offers_text if offers_text else "Nessuna offerta trovata."

    except NoCredentialsError:
        return "Errore: chiavi di accesso AWS non valide o mancanti."
    except Exception as e:
        return f"Errore nella richiesta: {str(e)}"

def send_telegram_message(message):
    """
    Invia un messaggio al canale Telegram configurato.
    """
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")

@app.route("/")
def home():
    return "🤖 Bot attivo"

@app.route("/fetch_offers")
def fetch_offers():
    offers = get_amazon_offers()
    send_telegram_message(offers)
    return "Offerte inviate!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
import sys
import time
import requests
import schedule
import subprocess

# Debug: Verifica l'ambiente di esecuzione
print("Percorso di Python:", sys.executable)
print("Percorso di esecuzione:", os.getcwd())
print("Variabili d'ambiente:", os.environ)

# Debug: Verifica se il modulo è installato
try:
    from python_amazon_paapi import AmazonAPI
    print("python_amazon_paapi è installato correttamente.")
except ImportError as e:
    print(f"Errore durante l'import di python_amazon_paapi: {e}")

# Debug: Elenca i moduli installati
print("Moduli installati:")
subprocess.run([sys.executable, "-m", "pip", "list"])

# Imposta le tue credenziali
TELEGRAM_TOKEN = "7213198162:AAHY9VfC-13x469C6psn3V36L1PGjCQxSs0"
CHAT_ID = "-1001434969904"
AMAZON_ACCESS_KEY = "AKPAV0YTNY1740423739"
AMAZON_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2hY"
AMAZON_ASSOCIATE_TAG = "new1707-21"

# Configura l'API di Amazon
try:
    amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOCIATE_TAG, "IT")
    print("API di Amazon configurata correttamente.")
except Exception as e:
    print(f"Errore durante la configurazione dell'API di Amazon: {e}")

# File per tenere traccia degli ASIN già inviati
SENT_ASINS_FILE = "sent_asins.txt"

def load_sent_asins():
    """Carica gli ASIN già inviati da un file."""
    if not os.path.exists(SENT_ASINS_FILE):
        return set()
    with open(SENT_ASINS_FILE, "r") as f:
        return set(f.read().splitlines())

def save_sent_asin(asin):
    """Salva un nuovo ASIN nel file."""
    with open(SENT_ASINS_FILE, "a") as f:
        f.write(asin + "\n")

def get_amazon_asins():
    """Simula il recupero di ASIN da Amazon (puoi sostituire questa logica con uno scraping reale)."""
    # Esempio di ASIN (sostituisci con la tua logica per ottenere ASIN reali)
    return ["B08N5WRWNW", "B09G3HRP7S"]

def get_product_info(asin):
    """Recupera le informazioni del prodotto utilizzando l'API di Amazon."""
    try:
        product = amazon.get_items(asin)
        if product and product.items:
            item = product.items[0]
            title = item.item_info.title.display_value if item.item_info.title else "Offerta Amazon"
            price = item.offers.listings[0].price.display_amount if item.offers else "N/A"
            image = item.images.primary.large.url if item.images and item.images.primary else None
            link = f"https://www.amazon.it/dp/{asin}?tag={AMAZON_ASSOCIATE_TAG}"
            return title, price, image, link
    except Exception as e:
        print(f"Errore nel recupero prodotto {asin}")

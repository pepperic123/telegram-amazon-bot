# Credenziali Amazon
AMAZON_ACCESS_KEY = "AKPAV0YTNY1740423739"
AMAZON_SECRET_KEY = "g0N1qt9tB2AUB+chkTDjakR3nafgqmkGkfr77/2h"
AMAZON_PARTNER_TAG = "new1707-21"
AMAZON_HOST = "webservices.amazon.it"  # Endpoint per l'Italia
AMAZON_RESOURCES = [
    "ItemInfo.Title",
    "Offers.Listings.Price",
    "Images.Primary.Large"
]

AMAZON_COUNTRY = "IT"  # Codice paese (es: "IT" per Italia)

# Credenziali Telegram
TELEGRAM_TOKEN = "7193847897:AAE7ny5YWjmPyrxIcgeCjvsy8koYM8jQ7pw"  # Token del bot Telegram
TELEGRAM_CHAT_ID = "-1001434969904"  # ID del chat o canale Telegram

# Credenziali GitHub (per memorizzare gli ASIN inviati)
GITHUB_REPO_URL = "https://raw.githubusercontent.com/pepperic123/telegram-amazon-bot/main/sent_asins.txt"  # URL del file su GitHub
GITHUB_UPDATE_URL = "https://api.github.com/repos/pepperic123/telegram-amazon-bot/contents/sent_asins.txt"  # URL API per aggiornare il file
GITHUB_TOKEN = ""  # Token Gi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tHub (revocalo se esposto)
# Categorie Amazon per la ricerca
AMAZON_CATEGORIES = [
    "Appliances",        # Elettrodomestici
    "ArtsAndCrafts",     # Arti e Mestieri
    "Automotive",        # Automotive
    "Baby",              # Bambini
    "Beauty",            # Bellezza
    "Books",             # Libri
    "Clothing",          # Abbigliamento
    "Electronics",       # Elettronica
    "Grocery",           # Alimentari
    "Health",            # Salute
    "Home",              # Casa
    "Industrial",        # Industria
    "Jewelry",           # Gioielleria
    "KindleStore",       # Kindle Store
    "Kitchen",           # Cucina
    "Luggage",           # Valigie
    "Music",             # Musica
    "OfficeProducts",    # Prodotti per ufficio
    "PersonalCare",      # Cura personale
    "Shoes",             # Scarpe
    "Software",          # Software
    "Sports",            # Sport
    "Tools",             # Attrezzi
    "Toys",              # Giochi
    "VideoGames",        # Videogiochi
    "Watches",           # Orologi
    "Women",             # Donne
    ]

from amazon_paapi import AmazonAPI
from config import (
    AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY,
    AMAZON_PARTNER_TAG, AMAZON_HOST, AMAZON_RESOURCES
)

class AmazonApiWrapper:
    def __init__(self):
        try:
            # Configura AmazonAPI
            self.api = AmazonAPI(
                AMAZON_ACCESS_KEY,
                AMAZON_SECRET_KEY,
                AMAZON_PARTNER_TAG,
                AMAZON_HOST
            )
            print("✅ API Amazon inizializzata correttamente.")
        except Exception as e:
            print(f"❌ Errore inizializzazione API: {str(e)}")
            self.api = None

    def get_offers(self, category):
        if not self.api:
            return []

        try:
            # Configura la richiesta per recuperare i prodotti
            items = self.api.search_items(
                keywords=category,
                resources=AMAZON_RESOURCES,  # Passa direttamente le risorse come stringhe
                item_count=10  # Numero di risultati
            )

            # Estrai i risultati
            offers = []
            if items:
                for item in items:
                    offer = {
                        "title": item.title,
                        "price": item.price_and_currency[0] if item.price_and_currency else "N/A",
                        "image": item.large_image_url if item.large_image_url else "N/A",
                        "link": item.detail_page_url,
                        "asin": item.asin
                    }
                    offers.append(offer)
            return offers

        except Exception as e:
            print(f"❌ Errore durante la richiesta: {str(e)}")
            return []

from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.search_items_request import SearchItemsRequest
from paapi5_python_sdk.rest import ApiException
from config import (
    AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY,
    AMAZON_PARTNER_TAG, AMAZON_HOST, AMAZON_RESOURCES
)

class AmazonApiWrapper:
    def __init__(self):
        try:
            self.api = DefaultApi(
                access_key=AMAZON_ACCESS_KEY,
                secret_key=AMAZON_SECRET_KEY,
                host=AMAZON_HOST,
                region="eu-west-1"  # Regione obbligatoria per l'Europa
            )
            print("✅ API Amazon inizializzata correttamente.")
        except Exception as e:
            print(f"❌ Errore inizializzazione API: {str(e)}")
            self.api = None

    def get_offers(self, category):
        if not self.api:
            return []

        try:
            # Configura la richiesta PAAPI 5.0
            request = SearchItemsRequest(
                partner_tag=AMAZON_PARTNER_TAG,
                partner_type="Associates",
                keywords=category,
                resources=AMAZON_RESOURCES,  # Passa direttamente le risorse come stringhe
                item_count=10  # Numero di risultati
            )

            # Esegui la chiamata
            response = self.api.search_items(request)

            # Estrai i risultati
            offers = []
            if response.search_result and response.search_result.items:
                for item in response.search_result.items:
                    offer = {
                        "title": item.item_info.title.display_value,
                        "price": item.offers.listings[0].price.display_amount if item.offers else "N/A",
                        "image": item.images.primary.large.url if item.images else "N/A",
                        "link": item.detail_page_url,
                        "asin": item.asin
                    }
                    offers.append(offer)
            return offers

        except ApiException as e:
            print(f"❌ Errore PAAPI 5.0: {e.body}")
            return []

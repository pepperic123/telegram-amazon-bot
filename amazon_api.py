# amazon_api.py
# Qui mettiamo solo la logica di interazione con l'API di Amazon

from amazon_paapi import AmazonApi

class AmazonApiWrapper:
    def __init__(self, access_key, secret_key, associate_tag, region, country):
        self.access_key = access_key
        self.secret_key = secret_key
        self.associate_tag = associate_tag
        self.region = region
        self.country = country
        self.amazon = AmazonApi(self.access_key, self.secret_key, self.associate_tag, self.region, self.country)

    def get_offers(self, category):
        try:
            response = self.amazon.get_items(
                search_index=category,
                item_count=10
            )
            if response and 'Items' in response:
                offers = []
                for item in response['Items']:
                    offer = {
                        'title': item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', ''),
                        'price': item.get('Offers', {}).get('Listings', [{}])[0].get('Price', {}).get('DisplayAmount', 'N/A'),
                        'link': item.get('DetailPageURL', ''),
                        'image': item.get('Images', {}).get('Primary', {}).get('Large', {}).get('URL', ''),
                        'asin': item.get('ASIN', '')
                    }
                    offers.append(offer)
                return offers
        except Exception as e:
            print(f"Errore nell'ottenere le offerte: {str(e)}")
        return []

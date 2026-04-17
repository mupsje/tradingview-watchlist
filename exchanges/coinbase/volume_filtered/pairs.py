import requests
from typing import List
import time

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    try:
        with requests.Session() as session:
            response = session.get('https://api.exchange.coinbase.com/products', timeout=15)
            response.raise_for_status()
            products = response.json()

            symbols = []
            for product in products:
                if product['status'] != 'online':
                    continue

                base = product['base_currency']
                quote = product['quote_currency']

                if quote_asset and quote != quote_asset:
                    continue

                # Rate limiting to avoid 503 errors
                time.sleep(0.1)

                try:
                    stats = session.get(
                        f'https://api.exchange.coinbase.com/products/{base}-{quote}/stats',
                        timeout=15
                    )
                    stats.raise_for_status()
                    stats_data = stats.json()
                    volume = float(stats_data.get('volume', 0) or 0) * float(stats_data.get('last', 0) or 0)

                    if min_volume and volume < min_volume:
                        continue

                    symbols.append(f'COINBASE:{base}{quote}')

                except (requests.RequestException, ValueError, KeyError):
                    continue

        return symbols

    except requests.RequestException as e:
        print(f"Error fetching Coinbase data: {e}")
        return []

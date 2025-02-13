import requests
from typing import List
import time

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    try:
        response = requests.get('https://api.exchange.coinbase.com/products')
        response.raise_for_status()
        
        symbols = []
        for product in response.json():
            if product['status'] != 'online':
                continue
                
            base = product['base_currency']
            quote = product['quote_currency']
            
            if quote_asset and quote != quote_asset:
                continue
                
            # Rate limiting to avoid 503 errors
            time.sleep(0.2)
            
            try:
                stats = requests.get(f'https://api.exchange.coinbase.com/products/{base}-{quote}/stats')
                stats.raise_for_status()
                stats_data = stats.json()
                volume = float(stats_data['volume']) * float(stats_data['last'])
                
                if min_volume and volume < min_volume:
                    continue
                    
                symbols.append(f'COINBASE:{base}{quote}')
                
            except (requests.RequestException, ValueError, KeyError):
                continue
        
        return symbols
        
    except requests.RequestException as e:
        print(f"Error fetching Coinbase data: {e}")
        return []

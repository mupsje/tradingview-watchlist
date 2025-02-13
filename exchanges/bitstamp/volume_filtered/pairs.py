import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    response = requests.get('https://www.bitstamp.net/api/v2/trading-pairs-info/')
    response.raise_for_status()
    pairs = response.json()
    
    symbols = []
    for pair in pairs:
        symbol = pair['url_symbol']
        if len(symbol) >= 6:
            base = symbol[:-3]
            quote = symbol[-3:]
            if quote_asset:
                if quote.upper() == quote_asset:
                    symbols.append(f'BITSTAMP:{base.upper()}{quote.upper()}')
            else:
                symbols.append(f'BITSTAMP:{base.upper()}{quote.upper()}')
    
    return symbols

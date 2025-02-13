import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    response = requests.get('https://api-pub.bitfinex.com/v2/tickers?symbols=ALL')
    response.raise_for_status()
    
    symbols = []
    for ticker in response.json():
        if not ticker[0].startswith('t'):
            continue
            
        symbol = ticker[0][1:]  # Remove 't' prefix
        if quote_asset:
            if symbol.endswith(quote_asset):
                symbols.append(f'BITFINEX:{symbol}')
        else:
            symbols.append(f'BITFINEX:{symbol}')
    
    return symbols

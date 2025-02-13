import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    response = requests.get('https://api.gateio.ws/api/v4/spot/tickers')
    response.raise_for_status()
    
    symbols = []
    for ticker in response.json():
        symbol = ticker['currency_pair']
        base, quote = symbol.split('_')
        volume = float(ticker['quote_volume']) * float(ticker['last'])
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and quote == quote_asset:
            symbols.append(f'GATEIO:{base}{quote}')
        elif not quote_asset:
            symbols.append(f'GATEIO:{base}{quote}')
    
    return symbols

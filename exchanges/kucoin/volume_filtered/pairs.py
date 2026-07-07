import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch KuCoin trading symbols with volume filter."""
    pairs_response = requests.get('https://api.kucoin.com/api/v1/symbols')
    tickers_response = requests.get('https://api.kucoin.com/api/v1/market/allTickers')
    
    pairs_response.raise_for_status()
    tickers_response.raise_for_status()
    
    pairs = pairs_response.json()['data']
    tickers = {t['symbol']: float(t['volValue']) for t in tickers_response.json()['data']['ticker']}
    
    symbols = []
    for pair in pairs:
        volume = tickers.get(pair['symbol'], 0)
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and pair['quoteCurrency'] != quote_asset.upper():
            continue
            
        symbols.append(f"KUCOIN:{pair['name'].upper().replace('-', '').replace('/', '')}")
    
    return sorted(symbols)

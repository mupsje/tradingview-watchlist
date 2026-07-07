import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Huobi trading symbols with volume filter."""
    symbols_response = requests.get('https://api.huobi.pro/v1/common/symbols')
    tickers_response = requests.get('https://api.huobi.pro/market/tickers')
    
    symbols_response.raise_for_status()
    tickers_response.raise_for_status()
    
    symbols = symbols_response.json()['data']
    tickers = {t['symbol']: float(t['vol']) * float(t['close']) for t in tickers_response.json()['data']}
    
    filtered_symbols = []
    for s in symbols:
        volume = tickers.get(s['symbol'], 0)
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and s['quote-currency'] != quote_asset.lower():
            continue
            
        filtered_symbols.append(f"HUOBI:{s['symbol'].upper()}")
    
    return sorted(filtered_symbols)

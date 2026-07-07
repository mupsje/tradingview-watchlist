import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Bybit spot trading symbols with volume filter."""
    url = 'https://api.bybit.com/v5/market/tickers'
    params = {'category': 'spot'}
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    symbols = []
    for item in response.json()['result']['list']:
        volume = float(item['volume24h']) * float(item['lastPrice'])  # Convert to USD volume
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and not item['symbol'].endswith(quote_asset.upper()):
            continue
            
        symbols.append(f"BYBIT:{item['symbol']}")
    
    return sorted(symbols)


def get_futures_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Bybit linear perpetual futures symbols with volume filter.
    
    Returns TradingView-format perpetual symbols with .P suffix,
    e.g. BYBIT:BTCUSDT.P
    """
    url = 'https://api.bybit.com/v5/market/tickers'
    params = {'category': 'linear'}
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    symbols = []
    for item in response.json()['result']['list']:
        volume = float(item['volume24h']) * float(item['lastPrice'])
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and not item['symbol'].endswith(quote_asset.upper()):
            continue
            
        symbols.append(f"BYBIT:{item['symbol']}.P")
    
    return sorted(symbols)

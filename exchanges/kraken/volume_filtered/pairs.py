import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Kraken spot trading symbols with volume filter."""
    pairs_response = requests.get('https://api.kraken.com/0/public/AssetPairs')
    ticker_response = requests.get('https://api.kraken.com/0/public/Ticker')
    
    pairs_response.raise_for_status()
    ticker_response.raise_for_status()
    
    pairs = pairs_response.json()['result']
    tickers = ticker_response.json()['result']
    
    asset_map = {
        'USD': 'ZUSD', 'EUR': 'ZEUR', 'GBP': 'ZGBP', 'CAD': 'ZCAD',
        'AUD': 'ZAUD', 'JPY': 'ZJPY', 'CHF': 'ZCHF',
        'BTC': 'XBT', 'USDT': 'USDT', 'ETH': 'XETH', 'USDC': 'USDC',
        'DAI': 'DAI', 'PYUSD': 'PYUSD', 'POL': 'POL',
        'XBT': 'XBT', 'ETH': 'XETH'
    }
    
    if quote_asset:
        quote_asset = asset_map.get(quote_asset, quote_asset)
    
    symbols = []
    for pair_name, pair_info in pairs.items():
        base = pair_info['base']
        quote = pair_info['quote']
        
        if quote_asset and quote != quote_asset:
            continue
            
        volume = float(tickers[pair_name]['v'][1]) * float(tickers[pair_name]['c'][0])
        if min_volume and volume < min_volume:
            continue
            
        base = 'BTC' if base == 'XBT' else base.replace('Z', '').replace('X', '')
        quote = 'BTC' if quote == 'XBT' else quote.replace('Z', '').replace('X', '')
        
        symbols.append(f'KRAKEN:{base}{quote}')
    
    return sorted(symbols)

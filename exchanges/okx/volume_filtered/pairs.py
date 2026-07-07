import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch OKX spot trading symbols with volume filter."""
    pairs_response = requests.get('https://www.okx.com/api/v5/public/instruments?instType=SPOT')
    tickers_response = requests.get('https://www.okx.com/api/v5/market/tickers?instType=SPOT')
    
    pairs_response.raise_for_status()
    tickers_response.raise_for_status()
    
    pairs = pairs_response.json()['data']
    tickers = {t['instId']: float(t['volCcy24h']) for t in tickers_response.json()['data']}
    
    symbols = []
    for pair in pairs:
        volume = tickers.get(pair['instId'], 0)
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and pair['quoteCcy'] != quote_asset:
            continue
            
        symbols.append(f"OKX:{pair['baseCcy']}{pair['quoteCcy']}")
    
    return sorted(symbols)

def get_futures_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch OKX perpetual swap symbols with volume filter.
    
    Returns TradingView-format SWAP symbols, e.g. OKX:BTC-USDT-SWAP.
    """
    pairs_response = requests.get('https://www.okx.com/api/v5/public/instruments?instType=SWAP')
    tickers_response = requests.get('https://www.okx.com/api/v5/market/tickers?instType=SWAP')
    
    pairs_response.raise_for_status()
    tickers_response.raise_for_status()
    
    pairs = pairs_response.json()['data']
    tickers = {t['instId']: float(t['volCcy24h']) for t in tickers_response.json()['data']}
    
    symbols = []
    for pair in pairs:
        volume = tickers.get(pair['instId'], 0)
        if min_volume and volume < min_volume:
            continue
        # Extract quote asset from instFamily (e.g. 'BTC-USD' -> quote='USD')
        inst_quote = pair['instFamily'].split('-')[-1] if '-' in pair.get('instFamily', '') else ''
        if quote_asset and inst_quote.upper() != quote_asset.upper():
            continue
        symbols.append(f"OKX:{pair['instId']}")
    
    return sorted(symbols)

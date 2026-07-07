import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch MEXC spot trading symbols."""
    response = requests.get('https://api.mexc.com/api/v3/ticker/24hr')
    response.raise_for_status()
    pairs = response.json()
    
    symbols = []
    for pair in pairs:
        symbol = pair['symbol']
        volume = float(pair['volume']) * float(pair['lastPrice'])
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset:
            if symbol.endswith(quote_asset):
                base = symbol[:-len(quote_asset)]
                symbols.append(f'MEXC:{base}{quote_asset}')
        else:
            symbols.append(f'MEXC:{symbol}')
    
    return sorted(symbols)

def get_futures_symbols(min_volume: float = None) -> List[str]:
    """Fetch MEXC futures trading symbols."""
    response = requests.get('https://contract.mexc.com/api/v1/contract/ticker')
    response.raise_for_status()
    pairs = response.json()['data']
    
    symbols = []
    for p in pairs:
        volume = float(p['amount24']) * float(p['lastPrice'])
        if min_volume and volume < min_volume:
            continue
        symbols.append(f'MEXC:{p["symbol"]}PERP')
    
    return sorted(symbols)


def get_leveraged_tokens(min_volume: float = None) -> List[str]:
    """Fetch MEXC leveraged tokens."""
    response = requests.get('https://api.mexc.com/api/v3/leveraged/tokens')
    response.raise_for_status()
    tokens = response.json()
    
    if min_volume:
        tickers = requests.get('https://api.mexc.com/api/v3/leveraged/ticker').json()
        volumes = {t['symbol']: float(t['volume']) * float(t['price']) for t in tickers}
        return sorted([f'MEXC:{t["symbol"]}' for t in tokens if volumes.get(t["symbol"], 0) >= min_volume])
    
    return sorted([f'MEXC:{t["symbol"]}' for t in tokens])


if __name__ == "__main__":
    main()

import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    products = requests.get('https://api.bitget.com/api/spot/v1/public/products')
    tickers = requests.get('https://api.bitget.com/api/spot/v1/market/tickers')

    products.raise_for_status()
    tickers.raise_for_status()

    pairs = products.json()['data']
    volumes = {t['symbol']: float(t['usdtVol']) for t in tickers.json()['data']}

    symbols = []
    for pair in pairs:
        symbol = f"{pair['baseCoin']}{pair['quoteCoin']}"
        volume = volumes.get(symbol, 0)

        if min_volume and volume < min_volume:
            continue

        if quote_asset:
            if pair['quoteCoin'] == quote_asset:
                symbols.append(f'BITGET:{symbol}')
        else:
            symbols.append(f'BITGET:{symbol}')

    return symbols

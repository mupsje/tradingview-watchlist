import os
import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    base_products = os.getenv('BITGET_SPOT_PRODUCTS_API', 'https://api.bitget.com/api/spot/v1/public/products')
    base_tickers = os.getenv('BITGET_SPOT_TICKERS_API', 'https://api.bitget.com/api/spot/v1/market/tickers')

    with requests.Session() as session:
        products = session.get(base_products, timeout=15)
        tickers = session.get(base_tickers, timeout=15)

        try:
            products.raise_for_status()
            tickers.raise_for_status()
        except requests.RequestException as e:
            print(f"Bitget API error: {e}")
            return []

        pairs = products.json().get('data', [])
        volumes = {t['symbol']: float(t.get('usdtVol', 0) or 0) for t in tickers.json().get('data', [])}

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

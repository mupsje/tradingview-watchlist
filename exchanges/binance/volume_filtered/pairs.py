import requests
from typing import List

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Binance spot trading symbols with volume filter."""
    try:
        response_tickers = requests.get('https://api.binance.com/api/v3/ticker/24hr')
        response_info = requests.get('https://api.binance.com/api/v3/exchangeInfo')

        response_tickers.raise_for_status()
        response_info.raise_for_status()

        tickers = {t['symbol']: t for t in response_tickers.json()}
        symbols_info = response_info.json()['symbols']

        symbols = []
        for s in symbols_info:
            if s['status'] != 'TRADING':
                continue

            if quote_asset and s['quoteAsset'] != quote_asset:
                continue

            ticker = tickers.get(s['symbol'], {})
            if min_volume and float(ticker.get('quoteVolume', 0)) < min_volume:
                continue

            symbols.append(f"BINANCE:{s['symbol']}")

        return symbols

    except requests.RequestException as e:
        print(f"Error fetching data from Binance API: {e}")
        return []


def get_futures_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Binance USDⓈ-M perpetual futures symbols with volume filter.
    
    Returns TradingView-format perpetual symbols with .P suffix,
    e.g. BINANCE:BTCUSDT.P
    """
    try:
        response_tickers = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr')
        response_info = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo')

        response_tickers.raise_for_status()
        response_info.raise_for_status()

        tickers = {t['symbol']: t for t in response_tickers.json()}
        symbols_info = response_info.json()['symbols']

        symbols = []
        for s in symbols_info:
            if s['status'] != 'TRADING':
                continue
            if s.get('contractType') != 'PERPETUAL':
                continue

            if quote_asset and s['quoteAsset'] != quote_asset:
                continue

            ticker = tickers.get(s['symbol'], {})
            if min_volume and float(ticker.get('quoteVolume', 0)) < min_volume:
                continue

            symbols.append(f"BINANCE:{s['symbol']}.P")

        return symbols

    except requests.RequestException as e:
        print(f"Error fetching data from Binance Futures API: {e}")
        return []

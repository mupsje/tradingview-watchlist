import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_futures_symbols(min_volume: float = None) -> List[str]:
    """Fetch Binance futures trading symbols with volume filter."""
    response = requests.get('https://fapi.binance.com/fapi/v1/ticker/24hr')
    response.raise_for_status()
    tickers = response.json()
    
    symbols = []
    for ticker in tickers:
        if min_volume and float(ticker['quoteVolume']) < min_volume:
            continue
        symbols.append(f"BINANCE:{ticker['symbol']}PERP")
    
    return symbols

def get_spot_symbols(margin: bool = False, quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Binance spot trading symbols with volume filter."""
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
            
        if margin and not s['isMarginTradingAllowed']:
            continue
            
        if quote_asset and s['quoteAsset'] != quote_asset:
            continue
            
        ticker = tickers.get(s['symbol'], {})
        if min_volume and float(ticker.get('quoteVolume', 0)) < min_volume:
            continue
            
        symbols.append(f"BINANCE:{s['symbol']}")
    
    return symbols

def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"binance_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Binance tickers formatter')
    parser.add_argument('-m', '--margin', action='store_true', help='Show margin pairs only')
    parser.add_argument('-f', '--futures', action='store_true', help='Show futures pairs')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in quote currency')
    
    args = parser.parse_args()

    
    try:
        if args.futures:
            symbols = get_futures_symbols(args.min_volume)
            save_to_file(symbols, 'futures')
        else:
            symbols = get_spot_symbols(args.margin, args.quote_asset, args.min_volume)
            market_type = 'margin' if args.margin else 'spot'
            save_to_file(symbols, market_type, args.quote_asset)
        
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Binance API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

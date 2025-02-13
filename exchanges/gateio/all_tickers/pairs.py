import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None) -> List[str]:
    """Fetch Gate.io spot trading symbols."""
    response = requests.get('https://api.gateio.ws/api/v4/spot/currency_pairs')
    response.raise_for_status()
    symbols = response.json()
    
    if quote_asset:
        symbols = [s for s in symbols if s['quote'] == quote_asset]
    
    return [f'GATEIO:{s["base"]}{s["quote"]}' for s in symbols if s['trade_status'] == 'tradable']

def get_futures_symbols() -> List[str]:
    """Fetch Gate.io futures trading symbols."""
    response = requests.get('https://api.gateio.ws/api/v4/futures/usdt/contracts')
    response.raise_for_status()
    symbols = response.json()
    return [f'GATEIO:{s["name"]}' for s in symbols if s['in_delisting'] == False]


def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"gateio_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Gate.io tickers formatter')
    parser.add_argument('-f', '--futures', action='store_true', help='Show futures pairs')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    
    args = parser.parse_args()
    
    try:
        if args.futures:
            symbols = get_futures_symbols()
            save_to_file(symbols, 'futures')
        else:
            symbols = get_spot_symbols(args.quote_asset)
            save_to_file(symbols, 'spot', args.quote_asset)
        
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Gate.io API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

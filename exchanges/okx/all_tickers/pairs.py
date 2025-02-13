import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None) -> List[str]:
    """Fetch OKX spot trading symbols."""
    response = requests.get('https://www.okx.com/api/v5/public/instruments?instType=SPOT')
    response.raise_for_status()
    symbols = response.json()['data']
    
    if quote_asset:
        symbols = [s for s in symbols if s['quoteCcy'] == quote_asset]
    
    return [f'OKX:{s["baseCcy"]}{s["quoteCcy"]}' for s in symbols]

def get_futures_symbols() -> List[str]:
    """Fetch OKX futures trading symbols."""
    response = requests.get('https://www.okx.com/api/v5/public/instruments?instType=SWAP')
    response.raise_for_status()
    symbols = response.json()['data']
    return [f'OKX:{s["instId"]}' for s in symbols]

def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"okx_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='OKX tickers formatter')
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
        print(f"Error fetching data from OKX API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

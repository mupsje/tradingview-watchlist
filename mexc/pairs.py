import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None) -> List[str]:
    """Fetch MEXC spot trading symbols."""
    response = requests.get('https://api.mexc.com/api/v3/ticker/24hr')
    response.raise_for_status()
    pairs = response.json()
    
    symbols = []
    for pair in pairs:
        symbol = pair['symbol']
        if quote_asset:
            if symbol.endswith(quote_asset):
                base = symbol[:-len(quote_asset)]
                symbols.append(f'MEXC:{base}{quote_asset}')
        else:
            symbols.append(f'MEXC:{symbol}')
    
    return symbols

def get_futures_symbols(perpetual: bool = False) -> List[str]:
    """Fetch MEXC futures trading symbols."""
    response = requests.get('https://contract.mexc.com/api/v1/contract/ticker')
    response.raise_for_status()
    pairs = response.json()['data']
    
    return [f'MEXC:{p["symbol"]}PERP' for p in pairs]


def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"mexc_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='MEXC tickers formatter')
    parser.add_argument('-f', '--futures', action='store_true', help='Show futures pairs')
    parser.add_argument('-p', '--perpetual', action='store_true', help='Show perpetual pairs')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    
    args = parser.parse_args()
    
    try:
        if args.futures or args.perpetual:
            symbols = get_futures_symbols(args.perpetual)
            market_type = 'perpetual' if args.perpetual else 'futures'
            save_to_file(symbols, market_type)
        else:
            symbols = get_spot_symbols(args.quote_asset)
            save_to_file(symbols, 'spot', args.quote_asset)
        
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from MEXC API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

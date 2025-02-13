import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None) -> List[str]:
    """Fetch Coinbase spot trading symbols."""
    response = requests.get('https://api.exchange.coinbase.com/products')
    response.raise_for_status()
    pairs = response.json()

    
    symbols = []
    for pair in pairs:
        if quote_asset:
            if pair['quote_currency'] == quote_asset:
                symbols.append(f"COINBASE:{pair['base_currency']}{pair['quote_currency']}")
        else:
            symbols.append(f"COINBASE:{pair['base_currency']}{pair['quote_currency']}")
    
    return sorted(symbols)

def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"coinbase_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Coinbase tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USD)')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset)
        save_to_file(symbols, 'spot', args.quote_asset)
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Coinbase API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

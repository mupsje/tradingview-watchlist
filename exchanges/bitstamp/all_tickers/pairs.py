import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None) -> List[str]:
    """Fetch Bitstamp spot trading symbols."""
    response = requests.get('https://www.bitstamp.net/api/v2/trading-pairs-info/')
    response.raise_for_status()
    pairs = response.json()
    
    symbols = []
    for pair in pairs:
        symbol = pair['url_symbol']
        if len(symbol) >= 6:
            base = symbol[:-3]
            quote = symbol[-3:]
            if quote_asset:
                if quote.upper() == quote_asset:
                    symbols.append(f'BITSTAMP:{base.upper()}{quote.upper()}')
            else:
                symbols.append(f'BITSTAMP:{base.upper()}{quote.upper()}')
    
    return symbols


def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"bitstamp_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Bitstamp tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USD)')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset)
        save_to_file(symbols, 'spot', args.quote_asset)
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Bitstamp API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

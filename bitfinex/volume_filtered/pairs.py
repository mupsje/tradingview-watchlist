import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Bitfinex spot trading symbols with volume filter."""
    tickers_response = requests.get('https://api-pub.bitfinex.com/v2/tickers?symbols=ALL')
    tickers_response.raise_for_status()
    
    symbols = []
    for ticker in tickers_response.json():
        if not ticker[0].startswith('t'):
            continue
            
        symbol = ticker[0][1:]  # Remove 't' prefix
        volume = float(ticker[8])  # Daily volume in USD
        
        # Skip test pairs
        if 'TEST' in symbol:
            continue
            
        if quote_asset:
            if symbol.endswith(quote_asset):
                if min_volume and volume < min_volume:
                    continue
                symbols.append(f'BITFINEX:{symbol}')
        else:
            if min_volume and volume < min_volume:
                continue
            symbols.append(f'BITFINEX:{symbol}')
    
    return symbols

def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None, min_volume: float = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else "") +
              (f" and minimum volume {min_volume}" if min_volume else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    volume_tag = f"_vol{int(min_volume)}" if min_volume else ""
    filename = f"bitfinex_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Bitfinex tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USD)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in USD')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset, args.min_volume)
        save_to_file(symbols, 'spot', args.quote_asset, args.min_volume)
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Bitfinex API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

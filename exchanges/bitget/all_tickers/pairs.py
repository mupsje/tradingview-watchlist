import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Bitget spot trading symbols with volume filter."""
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
    filename = f"bitget_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Bitget tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in USD')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset, args.min_volume)
        save_to_file(symbols, 'spot', args.quote_asset, args.min_volume)
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Bitget API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

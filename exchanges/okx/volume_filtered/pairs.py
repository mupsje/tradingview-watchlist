import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch OKX spot trading symbols with volume filter."""
    pairs_response = requests.get('https://www.okx.com/api/v5/public/instruments?instType=SPOT')
    tickers_response = requests.get('https://www.okx.com/api/v5/market/tickers?instType=SPOT')
    
    pairs_response.raise_for_status()
    tickers_response.raise_for_status()
    
    pairs = pairs_response.json()['data']
    tickers = {t['instId']: float(t['volCcy24h']) for t in tickers_response.json()['data']}
    
    symbols = []
    for pair in pairs:
        volume = tickers.get(pair['instId'], 0)
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and pair['quoteCcy'] != quote_asset:
            continue
            
        symbols.append(f"OKX:{pair['baseCcy']}{pair['quoteCcy']}")
    
    return sorted(symbols)

def get_futures_symbols(min_volume: float = None) -> List[str]:
    """Fetch OKX futures trading symbols with volume filter."""
    pairs_response = requests.get('https://www.okx.com/api/v5/public/instruments?instType=SWAP')
    tickers_response = requests.get('https://www.okx.com/api/v5/market/tickers?instType=SWAP')
    
    pairs_response.raise_for_status()
    tickers_response.raise_for_status()
    
    pairs = pairs_response.json()['data']
    tickers = {t['instId']: float(t['volCcy24h']) for t in tickers_response.json()['data']}
    
    symbols = []
    for pair in pairs:
        volume = tickers.get(pair['instId'], 0)
        if min_volume and volume < min_volume:
            continue
        symbols.append(f"OKX:{pair['instId']}")
    
    return sorted(symbols)

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
    filename = f"okx_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='OKX tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in quote currency')
    parser.add_argument('-f', '--futures', action='store_true', help='Show futures pairs')
    
    args = parser.parse_args()
    
    try:
        if args.futures:
            symbols = get_futures_symbols(args.min_volume)
            save_to_file(symbols, 'futures', args.quote_asset, args.min_volume)
        else:
            symbols = get_spot_symbols(args.quote_asset, args.min_volume)
            save_to_file(symbols, 'spot', args.quote_asset, args.min_volume)
        
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from OKX API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

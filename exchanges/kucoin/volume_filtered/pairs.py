import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch KuCoin trading symbols with volume filter."""
    pairs_response = requests.get('https://api.kucoin.com/api/v1/symbols')
    tickers_response = requests.get('https://api.kucoin.com/api/v1/market/allTickers')
    
    pairs_response.raise_for_status()
    tickers_response.raise_for_status()
    
    pairs = pairs_response.json()['data']
    tickers = {t['symbol']: float(t['volValue']) for t in tickers_response.json()['data']['ticker']}
    
    symbols = []
    for pair in pairs:
        volume = tickers.get(pair['symbol'], 0)
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and pair['quoteCurrency'] != quote_asset.upper():
            continue
            
        symbols.append(f"KUCOIN:{pair['name'].upper().replace('-', '').replace('/', '')}")
    
    return sorted(symbols)

def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None, min_volume: float = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else "") +
              (f" and minimum volume {min_volume}" if min_volume else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset.upper() if quote_asset else 'ALL'
    volume_tag = f"_vol{int(min_volume)}" if min_volume else ""
    filename = f"kucoin_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='KuCoin tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in quote currency')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset, args.min_volume)
        save_to_file(symbols, 'spot', args.quote_asset, args.min_volume)
        print(',\n'.join(symbols))
        
    except requests.RequestException as e:
        print(f"Error fetching data from KuCoin API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

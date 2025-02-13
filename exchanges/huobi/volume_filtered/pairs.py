import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Huobi trading symbols with volume filter."""
    symbols_response = requests.get('https://api.huobi.pro/v1/common/symbols')
    tickers_response = requests.get('https://api.huobi.pro/market/tickers')
    
    symbols_response.raise_for_status()
    tickers_response.raise_for_status()
    
    symbols = symbols_response.json()['data']
    tickers = {t['symbol']: float(t['vol']) * float(t['close']) for t in tickers_response.json()['data']}
    
    filtered_symbols = []
    for s in symbols:
        volume = tickers.get(s['symbol'], 0)
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset and s['quote-currency'] != quote_asset.lower():
            continue
            
        filtered_symbols.append(f"HUOBI:{s['symbol'].upper()}")
    
    return sorted(filtered_symbols)

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
    filename = f"huobi_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Huobi tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in quote currency')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset, args.min_volume)
        save_to_file(symbols, 'spot', args.quote_asset, args.min_volume)
        print(',\n'.join(symbols))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Huobi API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

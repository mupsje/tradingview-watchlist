import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch Kraken spot trading symbols with volume filter."""
    pairs_response = requests.get('https://api.kraken.com/0/public/AssetPairs')
    ticker_response = requests.get('https://api.kraken.com/0/public/Ticker')
    
    pairs_response.raise_for_status()
    ticker_response.raise_for_status()
    
    pairs = pairs_response.json()['result']
    tickers = ticker_response.json()['result']
    
    asset_map = {
        'USD': 'ZUSD', 'EUR': 'ZEUR', 'GBP': 'ZGBP', 'CAD': 'ZCAD',
        'AUD': 'ZAUD', 'JPY': 'ZJPY', 'CHF': 'ZCHF',
        'BTC': 'XBT', 'USDT': 'USDT', 'ETH': 'XETH', 'USDC': 'USDC',
        'DAI': 'DAI', 'PYUSD': 'PYUSD', 'POL': 'POL',
        'XBT': 'XBT', 'ETH': 'XETH'
    }
    
    if quote_asset:
        quote_asset = asset_map.get(quote_asset, quote_asset)
    
    symbols = []
    for pair_name, pair_info in pairs.items():
        base = pair_info['base']
        quote = pair_info['quote']
        
        if quote_asset and quote != quote_asset:
            continue
            
        volume = float(tickers[pair_name]['v'][1]) * float(tickers[pair_name]['c'][0])
        if min_volume and volume < min_volume:
            continue
            
        base = 'BTC' if base == 'XBT' else base.replace('Z', '').replace('X', '')
        quote = 'BTC' if quote == 'XBT' else quote.replace('Z', '').replace('X', '')
        
        symbols.append(f'KRAKEN:{base}{quote}')
    
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
    filename = f"kraken_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Kraken tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USD)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in quote currency')
    
    args = parser.parse_args()
    
    try:
        symbols = get_spot_symbols(args.quote_asset, args.min_volume)
        save_to_file(symbols, 'spot', args.quote_asset, args.min_volume)
        print(',\n'.join(symbols))
        
    except requests.RequestException as e:
        print(f"Error fetching data from Kraken API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

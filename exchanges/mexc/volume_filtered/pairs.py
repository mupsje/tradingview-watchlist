import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]:
    """Fetch MEXC spot trading symbols."""
    response = requests.get('https://api.mexc.com/api/v3/ticker/24hr')
    response.raise_for_status()
    pairs = response.json()
    
    symbols = []
    for pair in pairs:
        symbol = pair['symbol']
        volume = float(pair['volume']) * float(pair['lastPrice'])
        
        if min_volume and volume < min_volume:
            continue
            
        if quote_asset:
            if symbol.endswith(quote_asset):
                base = symbol[:-len(quote_asset)]
                symbols.append(f'MEXC:{base}{quote_asset}')
        else:
            symbols.append(f'MEXC:{symbol}')
    
    return sorted(symbols)

def get_futures_symbols(min_volume: float = None) -> List[str]:
    """Fetch MEXC futures trading symbols."""
    response = requests.get('https://contract.mexc.com/api/v1/contract/ticker')
    response.raise_for_status()
    pairs = response.json()['data']
    
    symbols = []
    for p in pairs:
        volume = float(p['amount24']) * float(p['lastPrice'])
        if min_volume and volume < min_volume:
            continue
        symbols.append(f'MEXC:{p["symbol"]}PERP')
    
    return sorted(symbols)


def get_leveraged_tokens(min_volume: float = None) -> List[str]:
    """Fetch MEXC leveraged tokens."""
    response = requests.get('https://api.mexc.com/api/v3/leveraged/tokens')
    response.raise_for_status()
    tokens = response.json()
    
    if min_volume:
        tickers = requests.get('https://api.mexc.com/api/v3/leveraged/ticker').json()
        volumes = {t['symbol']: float(t['volume']) * float(t['price']) for t in tickers}
        return sorted([f'MEXC:{t["symbol"]}' for t in tokens if volumes.get(t["symbol"], 0) >= min_volume])
    
    return sorted([f'MEXC:{t["symbol"]}' for t in tokens])

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
    filename = f"mexc_{market_type}_{asset_name}{volume_tag}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='MEXC tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    parser.add_argument('-v', '--min-volume', type=float, help='Minimum 24h volume in quote currency')
    parser.add_argument('-p', '--perpetual', action='store_true', help='Show perpetual pairs')
    parser.add_argument('-f', '--futures', action='store_true', help='Show futures pairs')
    
    args = parser.parse_args()
    
    try:
        if args.perpetual or args.futures:
            symbols = get_futures_symbols(args.min_volume)
            market_type = 'perpetual' if args.perpetual else 'futures'
        else:
            symbols = get_spot_symbols(args.quote_asset, args.min_volume)
            market_type = 'spot'
            
        save_to_file(symbols, market_type, args.quote_asset, args.min_volume)
        print(',\n'.join(sorted(symbols)))
        
    except requests.RequestException as e:
        print(f"Error fetching data from MEXC API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

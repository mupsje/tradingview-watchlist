import argparse
import requests
from typing import List
from datetime import datetime
import sys

def get_spot_symbols(quote_asset: str = None) -> List[str]:
    """Fetch Kraken spot trading symbols."""
    response = requests.get('https://api.kraken.com/0/public/AssetPairs')
    response.raise_for_status()
    pairs = response.json()['result']
    
    # Map common names to Kraken's internal names
    asset_map = {
        # Crypto-to-Cash markets
        'USD': 'ZUSD',
        'EUR': 'ZEUR',
        'GBP': 'ZGBP',
        'CAD': 'ZCAD',
        'AUD': 'ZAUD',
        'JPY': 'ZJPY',
        'CHF': 'ZCHF',
        
        # Crypto-to-Crypto markets
        'BTC': 'XBT',
        'USDT': 'USDT',
        'ETH': 'XETH',
        'USDC': 'USDC',
        'DAI': 'DAI',
        'PYUSD': 'PYUSD',
        'POL': 'POL',
        
        # Additional common mappings
        'XBT': 'XBT',
        'ETH': 'XETH'
    }

    
    if quote_asset:
        quote_asset = asset_map.get(quote_asset, quote_asset)
    
    symbols = []
    for pair_info in pairs.values():
        base = pair_info['base']
        quote = pair_info['quote']
        
        if quote_asset and quote != quote_asset:
            continue
            
        # Clean up the symbol names for TradingView
        base = 'BTC' if base == 'XBT' else base.replace('Z', '').replace('X', '')
        quote = 'BTC' if quote == 'XBT' else quote.replace('Z', '').replace('X', '')
        
        symbols.append(f'KRAKEN:{base}{quote}')
    
    return symbols

def get_futures_symbols(perpetual: bool = False) -> List[str]:
    """Fetch Kraken futures trading symbols."""
    response = requests.get('https://futures.kraken.com/derivatives/api/v3/instruments')
    response.raise_for_status()
    instruments = response.json()['instruments']
    
    if perpetual:
        return [f'KRAKEN:{s["symbol"]}' for s in instruments if s['tradeable'] and 'PERP' in s['symbol']]
    return [f'KRAKEN:{s["symbol"]}' for s in instruments if s['tradeable']]



def save_to_file(symbols: List[str], market_type: str, quote_asset: str = None):
    """Save symbols to a file."""
    if not symbols:
        print(f"No trading pairs found for {market_type.upper()}" + 
              (f" with {quote_asset}" if quote_asset else ""))
        sys.exit(1)
        
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    filename = f"kraken_{market_type}_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Kraken tickers formatter')
    parser.add_argument('-f', '--futures', action='store_true', help='Show futures pairs')
    parser.add_argument('-p', '--perpetual', action='store_true', help='Show perpetual pairs')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USD)')
    
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
        print(f"Error fetching data from Kraken API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

import argparse
import requests
from typing import List
from datetime import datetime

def get_huobi_symbols(quote_asset: str = None) -> List[str]:
    """Fetch and format Huobi trading symbols."""
    response = requests.get('https://api.huobi.pro/v1/common/symbols')
    response.raise_for_status()
    symbols = response.json()['data']

    if quote_asset:
        symbols = [s for s in symbols if s['quote-currency'] == quote_asset.lower()]
    
    formatted_symbols = [
        f"HUOBI:{s['symbol'].upper()}"
        for s in symbols
    ]
    
    return sorted(formatted_symbols)

def save_to_file(symbols: List[str], quote_asset: str = None):
    """Save symbols to a file with specified format."""
    current_date = datetime.now().strftime('%d-%b-%y').lower()    

    asset_name = quote_asset.upper() if quote_asset else 'all'
    filename = f"huobi_{asset_name}_pairs_{current_date}.txt"
    
    with open(filename, 'w') as f:
        f.write(',\n'.join(symbols))
    
    print(f"Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Huobi tickers formatter')
    parser.add_argument('-q', '--quote-asset', help='Filter by quote asset (e.g., USDT)')
    
    args = parser.parse_args()
    
    try:
        symbols = get_huobi_symbols(args.quote_asset)
        print(',\n'.join(symbols))
        save_to_file(symbols, args.quote_asset)
    except requests.RequestException as e:
        print(f"Error fetching data from Huobi API: {e}")
        exit(1)

if __name__ == "__main__":
    main()

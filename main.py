import argparse
import importlib
import os
import sys
from datetime import datetime

def save_pairs(symbols, exchange, quote_asset, min_volume):
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    asset_name = quote_asset if quote_asset else 'ALL'
    volume_dir = f"vol_{int(min_volume/1000)}K"
    output_dir = os.path.join('output', volume_dir)
    
    # Create directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{exchange}_{asset_name}_pairs_{current_date}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write(',\n'.join(sorted(symbols)))
    return filepath

def main():
    parser = argparse.ArgumentParser(description='Unified Crypto Exchange Watchlist Generator')
    parser.add_argument('--exchange', required=True, help='Exchange name')
    parser.add_argument('--quote-asset', help='Filter by quote asset')
    parser.add_argument('--min-volume', type=float, help='Minimum 24h volume')
    parser.add_argument('--debug', action='store_true', help='Show debug information')
    
    args = parser.parse_args()
    
    if args.debug:
        print(f"Python path: {sys.path}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir('.')}")
        print(f"Exchanges directory contents: {os.listdir('exchanges')}")
    
    exchange_module = importlib.import_module(f'exchanges.{args.exchange}.volume_filtered.pairs')
    symbols = exchange_module.get_spot_symbols(args.quote_asset, args.min_volume)
    print(f"Found {len(symbols)} pairs")
    
    if symbols:
        filepath = save_pairs(symbols, args.exchange, args.quote_asset, args.min_volume)
        print(f"Pairs saved to: {filepath}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Batch update all exchange data and generate analysis
"""
import subprocess
import sys
import time
import os
import glob
from datetime import datetime

# Configuration
from config import VOLUME_THRESHOLDS, get_volume_bucket_label

EXCHANGES = ["binance", "bitfinex", "bitget", "bitstamp", "bybit", "coinbase", "gateio", "huobi", "kraken", "kucoin", "mexc", "okx"]
FUTURES_EXCHANGES = ["binance", "bybit", "coinbase", "okx"]  # Exchanges with futures/perpetual support
QUOTE_ASSETS = ["USDT", "EUR", "USD", "BTC", "ETH"]
FUTURES_QUOTE_ASSETS = ["USDT", "USDC"]  # Perpetuals: most are USDT, Coinbase uses USDC

def clean_old_files():
    """Remove old data files"""
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    print(f"🧹 Cleaning old files (keeping {current_date})...")
    
    removed_count = 0
    
    # Clean crypto files (both spot and perpetual)
    for volume in VOLUME_THRESHOLDS:
        vol_dir = f"output/vol_{get_volume_bucket_label(volume)}"
        if os.path.exists(vol_dir):
            pattern = f"{vol_dir}/*pairs*.txt"
            for file_path in glob.glob(pattern):
                filename = os.path.basename(file_path)
                if current_date not in filename:
                    os.remove(file_path)
                    removed_count += 1
                    print(f"  🗑️  Removed: {filename}")
    
    # Clean forex and stocks files
    for data_dir in ["forex", "stocks"]:
        if os.path.exists(data_dir):
            pattern = f"{data_dir}/*.txt"
            for file_path in glob.glob(pattern):
                filename = os.path.basename(file_path)
                if current_date not in filename:
                    os.remove(file_path)
                    removed_count += 1
                    print(f"  🗑️  Removed: {filename}")
    
    print(f"✓ Removed {removed_count} old files\n")

def run_exchange_update(exchange, quote_asset, min_volume, futures=False):
    """Run single exchange update"""
    cmd = [
        sys.executable, "main.py",
        "--exchange", exchange,
        "--quote-asset", quote_asset,
        "--min-volume", str(min_volume)
    ]
    if futures:
        cmd.append("--futures")
    
    label = f"{exchange} {quote_asset} {'perp' if futures else 'spot'}"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0:
            # Extract pair count from output
            output_lines = result.stdout.strip().split('\n')
            pair_count = 0
            for line in output_lines:
                if "Found" in line and "pairs" in line:
                    try:
                        pair_count = int(line.split()[1])
                    except (ValueError, IndexError):
                        pass
                    break
            
            if pair_count > 0:
                print(f"✓ {label} ({pair_count} pairs)")
            else:
                print(f"○ {label} (0 pairs)")
            return True, pair_count
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            print(f"✗ {label} - {error_msg}")
            return False, 0
    except subprocess.TimeoutExpired:
        print(f"✗ {label} - Timeout")
        return False, 0
    except Exception as e:
        print(f"✗ {label} - {e}")
        return False, 0

def update_forex():
    """Update OANDA forex data"""
    print("\n💱 Updating Forex data...")
    try:
        result = subprocess.run([sys.executable, "oanda.py"], 
                              cwd="forex", capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ OANDA forex data updated")
            return True
        else:
            print(f"❌ OANDA forex failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ OANDA forex error: {e}")
        return False


def dedupe_volume_buckets():
    """Ensure symbols only appear in the highest qualifying volume bucket."""
    print("\n🧹 Deduping volume buckets...")
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    seen_symbols = set()

    for volume in sorted(VOLUME_THRESHOLDS, reverse=True):
        vol_dir = f"output/vol_{get_volume_bucket_label(volume)}"
        filename_pattern = os.path.join(vol_dir, f"*_pairs_{current_date}.txt")
        for file_path in sorted(glob.glob(filename_pattern)):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read().strip()
                if not content:
                    continue

                symbols = [line.strip() for line in content.split(',\n') if line.strip()]
                unique_symbols = [s for s in symbols if s not in seen_symbols]

                if len(unique_symbols) != len(symbols):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(',\n'.join(unique_symbols))
                    print(f"  Updated {os.path.basename(file_path)} ({len(unique_symbols)} unique symbols)")

                seen_symbols.update(symbols)
            except Exception as e:
                print(f"  Failed to dedupe {file_path}: {e}")


def update_stocks():
    """Update stock data"""
    print("\n📈 Updating Stock data...")
    try:
        result = subprocess.run([sys.executable, "nasdaqtrader.py", "-nq", "-nyse", "-arca"], 
                              cwd="stocks", capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ Stock data updated (NYSE, NASDAQ, ARCA)")
            return True
        else:
            print(f"❌ Stock data failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Stock data error: {e}")
        return False

def show_summary():
    """Show summary of created files"""
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    print(f"\n{'='*60}")
    print("📊 UPDATE COMPLETE!")
    print('='*60)
    print(f"\n📁 New files created today ({current_date}):")
    
    total_files = 0
    total_pairs = 0
    
    # Crypto files
    for volume in VOLUME_THRESHOLDS:
        vol_dir = f"output/vol_{get_volume_bucket_label(volume)}"
        if os.path.exists(vol_dir):
            pattern = f"{vol_dir}/*{current_date}*.txt"
            files = glob.glob(pattern)
            if files:
                print(f"\n📂 {vol_dir}/:")
                for file_path in sorted(files):
                    filename = os.path.basename(file_path)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read().strip()
                            pair_count = len(content.split('\n')) if content else 0
                        print(f"  📄 {filename} ({pair_count} pairs)")
                        total_files += 1
                        total_pairs += pair_count
                    except Exception as e:
                        print(f"  📄 {filename} (error reading: {e})")
    
    # Forex files
    forex_pattern = f"forex/*{current_date}*.txt"
    forex_files = glob.glob(forex_pattern)
    if forex_files:
        print(f"\n📂 forex/:")
        for file_path in sorted(forex_files):
            filename = os.path.basename(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read().strip()
                    pair_count = len(content.split('\n')) if content else 0
                print(f"  💱 {filename} ({pair_count} pairs)")
                total_files += 1
                total_pairs += pair_count
            except Exception as e:
                print(f"  💱 {filename} (error reading: {e})")

    # Stock files
    stock_pattern = f"stocks/*{current_date}*.txt"
    stock_files = glob.glob(stock_pattern)
    if stock_files:
        print(f"\n� stocks/:")
        for file_path in sorted(stock_files):
            filename = os.path.basename(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read().strip()
                    stock_count = len(content.split('\n')) if content else 0
                print(f"  �📈 {filename} ({stock_count} stocks)")
                total_files += 1
                total_pairs += stock_count
            except Exception as e:
                print(f"  📈 {filename} (error reading: {e})")
    
    # TradingView watchlist
    print(f"\n🎯 TradingView Exports:")
    master_watchlist = "output/tradingview_master_watchlist.txt"
    if os.path.exists(master_watchlist):
        try:
            with open(master_watchlist, 'r', encoding='utf-8') as f:
                symbol_count = len([l for l in f.readlines() if l.strip()])
            print(f"  ✓ tradingview_master_watchlist.txt ({symbol_count} symbols)")
        except Exception as e:
            print(f"  ✗ tradingview_master_watchlist.txt (error: {e})")
    
    per_exchange_dir = "output/crypto_rankings"
    if os.path.exists(per_exchange_dir):
        md_count = len(glob.glob(f"{per_exchange_dir}/*/*_top_20.md"))
        txt_count = len(glob.glob(f"{per_exchange_dir}/*/*_tradingview_import.txt"))
        if md_count > 0:
            print(f"  ✓ Per-exchange rankings: {md_count} Markdown files")
        if txt_count > 0:
            print(f"  ✓ Per-exchange imports: {txt_count} TXT files")
    
    print(f"\n📈 Summary: {total_files} files, {total_pairs:,} total instruments")
    print(f"📊 Charts: output/charts/")
    print(f"📋 Reports: output/*.md")
    print(f"🎯 TradingView: output/tradingview_master_watchlist.txt + output/crypto_rankings/*/")

def main():
    print(f"🚀 Starting batch update at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 Crypto Exchanges: {len(EXCHANGES)}")
    print(f"💰 Quote assets: {len(QUOTE_ASSETS)}")  
    print(f"📈 Volume thresholds: {len(VOLUME_THRESHOLDS)}")
    print(f"� Futures/perpetual exchanges: {len(FUTURES_EXCHANGES)}")
    print(f"💱 Forex: OANDA (3 types)")
    print(f"📈 Stocks: NYSE, NASDAQ, ARCA")
    print(f"🎯 Total spot combinations: {len(EXCHANGES) * len(QUOTE_ASSETS) * len(VOLUME_THRESHOLDS)}")
    print(f"🎯 Total perpetual combinations: {len(FUTURES_EXCHANGES) * len(FUTURES_QUOTE_ASSETS) * len(VOLUME_THRESHOLDS)}")
    print("-" * 60)
    
    # Clean old files first
    clean_old_files()
    
    success_count = 0
    total_count = 0
    total_pairs = 0
    
    try:
        # Update crypto exchanges (spot)
        for volume in VOLUME_THRESHOLDS:
            print(f"\n📊 Volume threshold: {volume:,}")
            
            for exchange in EXCHANGES:
                print(f"\n🏢 Processing {exchange}...")
                
                for quote in QUOTE_ASSETS:
                    total_count += 1
                    success, pair_count = run_exchange_update(exchange, quote, volume)
                    if success:
                        success_count += 1
                        total_pairs += pair_count
                    
                    # Rate limiting
                    time.sleep(0.5)
        
        dedupe_volume_buckets()
        
        # Update crypto exchanges (perpetual futures)
        print(f"\n{'='*50}")
        print(f"🔮 UPDATING PERPETUAL FUTURES (.P) SYMBOLS")
        print(f"{'='*50}")
        for volume in VOLUME_THRESHOLDS:
            print(f"\n📊 Volume threshold: {volume:,}")
            
            for exchange in FUTURES_EXCHANGES:
                print(f"\n🏢 Processing {exchange} perpetuals...")
                
                for quote in FUTURES_QUOTE_ASSETS:
                    total_count += 1
                    success, pair_count = run_exchange_update(exchange, quote, volume, futures=True)
                    if success:
                        success_count += 1
                        total_pairs += pair_count
                    
                    # Rate limiting
                    time.sleep(0.5)

        print("\n🧭 Building market-cap buckets...")
        try:
            subprocess.run([sys.executable, "marketcap_bucket.py"], check=True)
            print("✅ Market-cap buckets created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Market-cap bucketing failed: {e}")
        except FileNotFoundError:
            print("❌ Market-cap script not found")
        
        # Update forex
        update_forex()
        
        # Update stocks  
        update_stocks()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted by user!")
        print(f"Progress: {success_count}/{total_count} completed")
    
    print(f"\n{'='*50}")
    print(f"📊 Final Statistics:")
    print(f"✅ Success: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}")
    print(f"📈 Total pairs: {total_pairs:,}")
    
    # Generate analysis
    print(f"\n📈 Generating analysis...")
    try:
        subprocess.run([sys.executable, "analysis/visualize.py"], check=True)
        print("✅ Analysis complete!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Analysis failed: {e}")
    except FileNotFoundError:
        print("❌ Analysis script not found")
    
    show_summary()

if __name__ == "__main__":
    main()
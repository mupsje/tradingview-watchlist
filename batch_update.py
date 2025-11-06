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
EXCHANGES = ["binance", "bitfinex", "bitget", "bitstamp", "bybit", "coinbase", "gateio", "huobi", "kraken", "kucoin", "mexc", "okx"]
QUOTE_ASSETS = ["USDT", "EUR", "USD", "BTC", "ETH"]
VOLUME_THRESHOLDS = [500000, 1000000, 5000000]

def clean_old_files():
    """Remove old data files"""
    current_date = datetime.now().strftime('%d-%b-%y').lower()
    print(f"🧹 Cleaning old files (keeping {current_date})...")
    
    removed_count = 0
    
    # Clean crypto files
    for volume in VOLUME_THRESHOLDS:
        vol_dir = f"output/vol_{int(volume/1000)}K"
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

def run_exchange_update(exchange, quote_asset, min_volume):
    """Run single exchange update"""
    cmd = [
        sys.executable, "main.py",
        "--exchange", exchange,
        "--quote-asset", quote_asset,
        "--min-volume", str(min_volume)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            # Extract pair count from output
            output_lines = result.stdout.strip().split('\n')
            pair_count = 0
            for line in output_lines:
                if "Found" in line and "pairs" in line:
                    pair_count = int(line.split()[1])
                    break
            
            if pair_count > 0:
                print(f"✓ {exchange} {quote_asset} ({pair_count} pairs)")
            else:
                print(f"○ {exchange} {quote_asset} (0 pairs)")
            return True, pair_count
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            print(f"✗ {exchange} {quote_asset} - {error_msg}")
            return False, 0
    except subprocess.TimeoutExpired:
        print(f"✗ {exchange} {quote_asset} - Timeout")
        return False, 0
    except Exception as e:
        print(f"✗ {exchange} {quote_asset} - {e}")
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

def update_stocks():
    """Update stock data"""
    print("\n📈 Updating Stock data...")
    try:
        result = subprocess.run([sys.executable, "nasdaqtrader.py"], 
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
        vol_dir = f"output/vol_{int(volume/1000)}K"
        if os.path.exists(vol_dir):
            pattern = f"{vol_dir}/*{current_date}*.txt"
            files = glob.glob(pattern)
            if files:
                print(f"\n📂 {vol_dir}/:")
                for file_path in sorted(files):
                    filename = os.path.basename(file_path)
                    try:
                        with open(file_path, 'r') as f:
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
                with open(file_path, 'r') as f:
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
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    stock_count = len(content.split('\n')) if content else 0
                print(f"  �📈 {filename} ({stock_count} stocks)")
                total_files += 1
                total_pairs += stock_count
            except Exception as e:
                print(f"  📈 {filename} (error reading: {e})")
    
    print(f"\n📈 Summary: {total_files} files, {total_pairs:,} total instruments")
    print(f"📊 Charts: output/charts/")
    print(f"📋 Reports: output/*.md")

def main():
    print(f"🚀 Starting batch update at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 Crypto Exchanges: {len(EXCHANGES)}")
    print(f"💰 Quote assets: {len(QUOTE_ASSETS)}")  
    print(f"📈 Volume thresholds: {len(VOLUME_THRESHOLDS)}")
    print(f"💱 Forex: OANDA (3 types)")
    print(f"📈 Stocks: NYSE, NASDAQ, ARCA")
    print(f"🎯 Total crypto combinations: {len(EXCHANGES) * len(QUOTE_ASSETS) * len(VOLUME_THRESHOLDS)}")
    print("-" * 60)
    
    # Clean old files first
    clean_old_files()
    
    success_count = 0
    total_count = 0
    total_pairs = 0
    
    try:
        # Update crypto exchanges
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
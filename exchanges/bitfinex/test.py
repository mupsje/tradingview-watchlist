import requests
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

class BitfinexPrice:
    def __init__(self):
        bitfinex_file = list(Path('output/vol_1000K').glob('bitfinex_USD_pairs_*.txt'))[0]
        with open(bitfinex_file, 'r') as f:
            # Remove BITFINEX: prefix and strip commas
            self.symbols = [pair.replace('BITFINEX:', '').strip(',') for pair in f.read().splitlines()]
        
    def get_price_data(self):
        results = []
        for symbol in self.symbols:
            try:
                url = f"https://api.bitfinex.com/v1/pubticker/{symbol.lower()}"
                response = requests.get(url)
                data = response.json()
                
                results.append({
                    'symbol': symbol,
                    'mid': float(data['mid']),
                    'bid': float(data['bid']),
                    'ask': float(data['ask']),
                    'last_price': float(data['last_price']),
                    'low': float(data['low']),
                    'high': float(data['high']),
                    'volume': float(data['volume']),
                    'timestamp': datetime.fromtimestamp(float(data['timestamp']))
                })
                print(f"Success: {symbol}")
                time.sleep(1)  # Rate limit protection
                
            except Exception as e:
                print(f"Error with {symbol}: {str(e)}")
                
        return pd.DataFrame(results)

if __name__ == "__main__":
    bitfinex = BitfinexPrice()
    df = bitfinex.get_price_data()
    output_file = 'output/bitfinex_prices.csv'
    df.to_csv(output_file, index=False)
    print(f"\nData saved to {output_file}")
    print(df)

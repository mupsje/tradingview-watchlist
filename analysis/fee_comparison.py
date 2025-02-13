import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define exchange fee structures
fee_data = {
    'exchange': [
        'Binance', 'Bitfinex', 'Bitget', 'Bitstamp', 'Bybit',
        'Coinbase', 'GateIO', 'Huobi', 'Kraken', 'Kucoin', 'MEXC', 'OKX'
    ],
    'maker_fee': [
        0.10, 0.10, 0.10, 0.30, 0.10,
        0.40, 0.20, 0.20, 0.16, 0.10, 0.20, 0.08
    ],
    'taker_fee': [
        0.10, 0.20, 0.15, 0.50, 0.15,
        0.60, 0.20, 0.20, 0.26, 0.10, 0.20, 0.10
    ],
    'withdrawal_fee_btc': [
        0.0005, 0.0004, 0.0005, 0.0005, 0.0003,
        0.0005, 0.0004, 0.0004, 0.0005, 0.0005, 0.0005, 0.0005
    ]
}

def analyze_fees():
    df = pd.DataFrame(fee_data)
    
    # Calculate total cost metrics
    df['avg_trading_fee'] = (df['maker_fee'] + df['taker_fee']) / 2
    df['cost_rating'] = df['avg_trading_fee'] * 0.7 + (df['withdrawal_fee_btc'] * 10000) * 0.3
    
    # Generate visualizations
    plt.figure(figsize=(15, 10))
    
    # Trading fees comparison
    plt.subplot(2, 1, 1)
    x = range(len(df['exchange']))
    width = 0.35
    plt.bar(x, df['maker_fee'], width, label='Maker Fee')
    plt.bar([i + width for i in x], df['taker_fee'], width, label='Taker Fee')
    plt.xticks([i + width/2 for i in x], df['exchange'], rotation=45)
    plt.title('Trading Fee Comparison Across Exchanges')
    plt.ylabel('Fee Percentage (%)')
    plt.legend()
    
    # Save results
    plt.tight_layout()
    plt.savefig('output/charts/fee_comparison.png')
    
    # Generate markdown report
    report = """# Exchange Fee Analysis

## Trading Fee Rankings (Lowest to Highest)
"""
    # Sort exchanges by average trading fee
    ranked_fees = df.sort_values('avg_trading_fee')
    for _, row in ranked_fees.iterrows():
        report += f"\n### {row['exchange']}"
        report += f"\n- Maker Fee: {row['maker_fee']}%"
        report += f"\n- Taker Fee: {row['taker_fee']}%"
        report += f"\n- BTC Withdrawal: {row['withdrawal_fee_btc']} BTC"
    
    with open('output/fee_analysis.md', 'w') as f:
        f.write(report)

if __name__ == "__main__":
    analyze_fees()

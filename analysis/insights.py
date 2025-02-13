import pandas as pd
from pathlib import Path

def generate_insights():
    data = []
    # Load data from files
    for volume_dir in Path("output").glob("vol_*K"):
        volume = int(volume_dir.name.replace("vol_", "").replace("K", "000"))
        for file in volume_dir.glob("*_pairs_*.txt"):
            pairs = file.read_text().splitlines()
            exchange, quote, *_ = file.name.split("_")
            data.append({
                "exchange": exchange.upper(),
                "quote": quote,
                "volume": volume,
                "pairs": pairs,
                "pair_count": len(pairs)
            })

    df = pd.DataFrame(data)

    # Generate insights report
    report = """# Trading Pairs Analysis Insights

## Highest Volume Trading Activity
"""
    # 5M volume pairs by exchange
    high_volume = df[df['volume'] == 5000000].sort_values('pair_count', ascending=False)
    report += "\nExchanges with most 5M+ volume pairs:\n"
    for _, row in high_volume.head().iterrows():
        report += f"- {row['exchange']}: {row['pair_count']} pairs\n"

    report += "\n## Exchange Diversity\n"
    diversity = df.groupby('exchange')['pair_count'].sum().sort_values(ascending=False)
    report += "\nMost diverse exchanges (total pairs):\n"
    for exchange, count in diversity.head().items():
        report += f"- {exchange}: {count} total pairs\n"

    report += "\n## Quote Asset Dominance\n"
    quote_dominance = df.groupby('quote')['pair_count'].sum().sort_values(ascending=False)
    report += "\nMost used quote assets:\n"
    for quote, count in quote_dominance.items():
        percentage = (count / quote_dominance.sum()) * 100
        report += f"- {quote}: {count} pairs ({percentage:.1f}%)\n"

    # Save insights
    Path("output/insights.md").write_text(report)
    print("Insights generated in output/insights.md")

if __name__ == "__main__":
    generate_insights()

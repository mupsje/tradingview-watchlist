import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for better-looking charts
plt.style.use('default')
sns.set_theme()

# Create charts directory
Path("output/charts").mkdir(exist_ok=True)

# Load and process data
data = []
VOLUME_DIR_MAP = {
    '500K-1000K': 500000,
    '1M-5M': 1000000,
    '5M+': 5000000
}
for volume_dir in Path("output").glob("vol_*"):
    bucket_label = volume_dir.name.replace("vol_", "")
    volume = VOLUME_DIR_MAP.get(bucket_label)
    if volume is None:
        if bucket_label.endswith('+'):
            volume = int(bucket_label[:-1].replace('M', '000000').replace('K', '000'))
        elif '-' in bucket_label:
            volume = int(bucket_label.split('-')[0].replace('M', '000000').replace('K', '000'))
        else:
            volume = int(bucket_label.replace('M', '000000').replace('K', '000'))

    for file in volume_dir.glob("*_pairs_*.txt"):
        content = file.read_text(encoding='utf-8', errors='replace').strip()
        pairs = len(content.splitlines()) if content else 0
        exchange, quote, *_ = file.name.split("_")
        data.append({
            "exchange": exchange.upper(),
            "quote": quote,
            "volume": volume,
            "pairs": pairs
        })

df = pd.DataFrame(data)

# 1. Exchange Pairs Chart
plt.figure(figsize=(15, 8))
total_pairs = df.groupby("exchange")["pairs"].sum().sort_values(ascending=False)
sns.barplot(x=total_pairs.index, y=total_pairs.values)
plt.title("Total Trading Pairs by Exchange", pad=20)
plt.xticks(rotation=45)
plt.ylabel("Number of Pairs")
plt.tight_layout()
plt.savefig("output/charts/exchange_pairs.png")

# 2. Volume Threshold Comparison
plt.figure(figsize=(15, 8))
volume_pivot = df.pivot_table(
    index="exchange", 
    columns="volume",
    values="pairs",
    aggfunc="sum"
).fillna(0)
volume_pivot.plot(kind="bar", width=0.8)
plt.title("Pairs Count by Volume Threshold", pad=20)
plt.xlabel("Exchange")
plt.ylabel("Number of Pairs")
plt.legend(title="Volume Threshold ($)", labels=["500K", "1M", "5M"])
plt.tight_layout()
plt.savefig("output/charts/volume_comparison.png")

# 3. Quote Asset Distribution
plt.figure(figsize=(15, 8))
quote_pivot = df.pivot_table(
    index="exchange",
    columns="quote",
    values="pairs",
    aggfunc="sum"
).fillna(0)
quote_pivot.plot(kind="bar", stacked=True)
plt.title("Quote Asset Distribution by Exchange", pad=20)
plt.xlabel("Exchange")
plt.ylabel("Number of Pairs")
plt.legend(title="Quote Asset", bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig("output/charts/quote_distribution.png")

print("Charts generated successfully in output/charts/")

# tradingview-watchlist

A generator for TradingView watchlists that fetches exchange symbol data, filters by quote asset and volume, and writes range-based output files for analysis.

## What it does

- Loads exchange-specific symbol crawlers from `exchanges/*/volume_filtered/pairs.py`
- Filters spot symbols by quote asset and 24h volume
- Writes TradingView-ready symbol lists into `output/vol_<bucket>/`
- Supports chart/report generation via `analysis/`

## Usage

Generate one exchange watchlist:

```powershell
python main.py --exchange <exchange> --quote-asset <asset> --min-volume <amount>
```

Run the full update pipeline:

```powershell
python batch_update.py
```

Generate analysis manually:

```powershell
python analysis\visualize.py
python analysis\insights.py
python analysis\fee_comparison.py
```

## Output layout

Generated files are stored by volume bucket:

- `output/vol_500K-1000K/`
- `output/vol_1M-5M/`
- `output/vol_5M+/`

Each file is named like:

- `exchange_quote_pairs_<date>.txt`

Analysis outputs include:

- `output/charts/`
- `output/insights.md`
- `output/fee_analysis.md`

## Project structure

- `main.py` — central CLI and save logic
- `batch_update.py` — batch runner for crypto exchanges, forex, stocks, and analysis
- `exchanges/` — exchange-specific symbol fetchers
- `analysis/` — visualization and insight scripts
- `forex/` and `stocks/` — additional asset sources
- `requirements.txt` — Python dependencies

## Extending exchanges

Exchange modules must expose:

```python
get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]
```

Returned symbols should already be TradingView-formatted, for example `BINANCE:ETHUSDT`.

> [!note]
> Use `python main.py --exchange <exchange> --quote-asset USDT --min-volume 1000000` to validate a new exchange module.

## Docker

The repository includes a minimal `dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
VOLUME /app/output
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "main.py"]
```

Run with:

```powershell
docker build -t tradingview-watchlist .
docker run --rm -v ${PWD}\output:/app/output tradingview-watchlist --exchange binance --quote-asset USDT --min-volume 1000000
```

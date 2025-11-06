## Purpose
This repository generates TradingView watchlists (text files) by querying exchange APIs and filtering by quote asset and 24h volume. The AI agent should focus on the orchestration in `main.py`, the exchange-specific modules under `exchanges/`, and the downstream `analysis/` scripts that consume `output/`.

## Big-picture architecture (quick)
- Entrypoint: `main.py` — parses CLI args and dynamically imports `exchanges.<exchange>.volume_filtered.pairs`.
- Exchange modules: `exchanges/<exchange>/{all_tickers,volume_filtered}/pairs.py` implement `get_spot_symbols(...)` and sometimes `get_futures_symbols(...)`. They return List[str] of TradingView-formatted symbols (e.g. `OKX:BTCUSDT`).
- Output: `output/vol_<N>K/` contains generated `*_pairs_*.txt` files used by `analysis/` for charts and reports.
- Analysis: `analysis/*.py` (e.g., `visualize.py`, `insights.py`) read `output/` files and produce markdown and charts under `output/`.

## Key conventions to follow
- Function signature: volume-filtered modules implement `get_spot_symbols(quote_asset: str = None, min_volume: float = None) -> List[str]`. Keep this signature when adding exchanges.
- All exchange modules use `requests` for HTTP calls and typically raise `requests.RequestException`; callers often catch and exit.
- File naming: `exchange_quote_pairs_<date>.txt` or similar — `main.py` writes into `output/vol_<int(min_volume/1000)>K/`.
- Symbol format: return strings already prefixed for TradingView (e.g., `BINANCE:ETHUSDT` or `OKX:BTCUSDT`). Do not transform further downstream.

## Common tasks and examples
- Run generator for an exchange (pwsh / Windows):
  python .\main.py --exchange okx --quote-asset USDT --min-volume 1000000
- Debug run (prints paths and directories):
  python .\main.py --exchange binance --debug
- Add a new exchange: create `exchanges/<name>/volume_filtered/pairs.py` and implement `get_spot_symbols(...)`. Follow the pattern in `exchanges/okx/volume_filtered/pairs.py`.

## Files to inspect when changing behavior
- `main.py` — CLI, dynamic import, and `save_pairs()` logic.
- `exchanges/*/volume_filtered/pairs.py` and `exchanges/*/all_tickers/pairs.py` — API calls and per-exchange data mapping.
- `analysis/visualize.py` — how output files are parsed and how charts are generated.
- `requirements.txt` — pinned deps (requests, pandas, python-dotenv).

## Testing and debug guidance
- No unit test harness is present. Use the CLI to test exchanges.
- For network issues, look at how individual exchange modules call `raise_for_status()` and wrap calls in try/except for `requests.RequestException`.
- When adding functionality, run a quick manual end-to-end: generate pairs for one exchange and confirm files appear in `output/vol_*K/` and `analysis/visualize.py` can read them.

## Non-obvious project-specific notes
- There are two parallel implementations per exchange: `all_tickers` (no volume filter) and `volume_filtered` (uses ticker volume). Choose the correct folder when implementing filters.
- Volume thresholds in `main.py` are interpreted as raw numbers (e.g., 1000000 => `vol_1000K`). The rounding convention is integer division by 1000 for folder names.
- `analysis/` expects `vol_*K` folders and file name tokens to parse exchange and quote asset. Keep filename patterns consistent.

## When opening PRs
- Preserve existing file naming and `get_spot_symbols` signatures.
- Add a small example run in the PR description showing the CLI command used and the output file path.

If any part of the repo is unclear or you'd like this trimmed/expanded, tell me which section to iterate on.

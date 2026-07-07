#!/usr/bin/env python3
"""Create market-cap filtered copies and a combined crypto summary report."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from config import VOLUME_BUCKETS
CAP_BUCKETS: List[Tuple[str, int, Optional[int]]] = [
    ("10M-100M", 10_000_000, 100_000_000),
    ("100M-500M", 100_000_000, 500_000_000),
    ("500M+", 500_000_000, None),
]
MIN_MARKET_CAP = CAP_BUCKETS[0][1]
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
BLACKLIST_PATH = Path("crypto_blacklist.txt")
OUTPUT_DIR = Path("output")


@dataclass(frozen=True)
class BucketResult:
    bucket_label: str
    file_path: Path
    symbol_count: int


@dataclass(frozen=True)
class SymbolRecord:
    exchange: str
    quote_asset: str
    volume_bucket: str
    source_file: Path
    tv_symbol: str
    base_symbol: str
    market_cap: float
    cap_bucket: str


@dataclass(frozen=True)
class RankedRecord:
    exchange: str
    symbol: str
    quote_asset: str
    volume_bucket: str
    cap_bucket: str
    market_cap: float
    rank_score: int
    source_file: Path


VOLUME_PRIORITY = {
    "5M+": 3,
    "1M-5M": 2,
    "500K-1000K": 1,
}

CAP_PRIORITY = {
    "10M-100M": 3,
    "100M-500M": 2,
    "500M+": 1,
}


def fetch_market_caps() -> Dict[str, float]:
    """Fetch a symbol -> market cap map from CoinGecko."""
    session = requests.Session()
    symbol_caps: Dict[str, float] = {}
    page = 1

    while True:
        response = None
        for attempt in range(4):
            response = session.get(
                COINGECKO_URL,
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": page,
                    "sparkline": "false",
                },
                timeout=60,
            )
            if response.status_code != 429:
                break

            wait_seconds = int(response.headers.get("Retry-After", "10"))
            time.sleep(wait_seconds + attempt)

        if response is None:
            break

        response.raise_for_status()
        coins = response.json()
        if not coins:
            break

        page_min_cap: Optional[float] = None

        for coin in coins:
            symbol = str(coin.get("symbol", "")).strip().lower()
            market_cap = coin.get("market_cap")
            if not symbol or market_cap is None:
                continue

            if page_min_cap is None or market_cap < page_min_cap:
                page_min_cap = float(market_cap)

            current_cap = symbol_caps.get(symbol)
            if current_cap is None or market_cap > current_cap:
                symbol_caps[symbol] = float(market_cap)

        if page_min_cap is not None and page_min_cap < MIN_MARKET_CAP:
            break

        if len(coins) < 250:
            break

        page += 1
        time.sleep(1.0)

    return symbol_caps


def read_symbols(file_path: Path) -> List[str]:
    content = file_path.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        return []
    return [line.strip() for line in content.split(",\n") if line.strip()]


def read_blacklist() -> set[str]:
    if not BLACKLIST_PATH.exists():
        return set()

    blocked: set[str] = set()
    for raw_line in BLACKLIST_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip().lower()
        if not line or line.startswith("#"):
            continue
        blocked.add(line)
    return blocked


def extract_blacklist_key(symbol: str, quote_asset: str) -> str:
    """Extract the base symbol for blacklist checking, handling .P suffix."""
    if ":" in symbol:
        core = symbol.split(":", 1)[1]
    else:
        core = symbol
    if core.endswith(".P"):
        core = core[:-2]
    if core.upper().endswith(quote_asset.upper()):
        core = core[:-len(quote_asset)]
    return core


def extract_base_symbol(tv_symbol: str, quote_asset: str) -> Optional[str]:
    core = tv_symbol.split(":", 1)[-1].strip()
    # Strip .P suffix for perpetual futures
    if core.endswith(".P"):
        core = core[:-2]
    quote_asset = quote_asset.upper()
    if not core.endswith(quote_asset):
        return None
    base = core[: -len(quote_asset)]
    return base or None


def matches_cap_bucket(market_cap: float, min_cap: int, max_cap: Optional[int]) -> bool:
    if market_cap < min_cap:
        return False
    if max_cap is not None and market_cap >= max_cap:
        return False
    return True


def get_cap_bucket_label(market_cap: float) -> Optional[str]:
    for label, min_cap, max_cap in CAP_BUCKETS:
        if matches_cap_bucket(market_cap, min_cap, max_cap):
            return label
    return None


def score_record(volume_bucket: str, cap_bucket: str) -> int:
    return (CAP_PRIORITY.get(cap_bucket, 0) * 10) + VOLUME_PRIORITY.get(volume_bucket, 0)


def clean_existing_cap_files() -> None:
    for volume_bucket in VOLUME_BUCKETS:
        base_dir = OUTPUT_DIR / f"vol_{volume_bucket}"
        if not base_dir.exists():
            continue
        for cap_label, _, _ in CAP_BUCKETS:
            cap_dir = base_dir / f"cap_{cap_label}"
            if cap_dir.exists():
                for old_file in cap_dir.glob("*.txt"):
                    old_file.unlink(missing_ok=True)


def clean_previous_reports() -> None:
    for report_name in [
        "crypto_marketcap_summary.csv",
        "crypto_marketcap_summary.md",
        "crypto_exchange_rankings.csv",
        "crypto_exchange_rankings.md",
        "tradingview_master_watchlist.txt",
    ]:
        report_path = OUTPUT_DIR / report_name
        if report_path.exists():
            report_path.unlink()
    
    rankings_dir = OUTPUT_DIR / "crypto_rankings"
    if rankings_dir.exists():
        for subdir in rankings_dir.iterdir():
            if subdir.is_dir():
                for file in subdir.glob("*.md"):
                    file.unlink(missing_ok=True)
                for file in subdir.glob("*.txt"):
                    file.unlink(missing_ok=True)


def parse_source_metadata(source_file: Path) -> Tuple[str, str, str]:
    parts = source_file.stem.split("_")
    if len(parts) < 4:
        return ("unknown", "ALL", "unknown")
    exchange = parts[0]
    quote_asset = parts[1]
    volume_bucket = source_file.parent.name.replace("vol_", "")
    return exchange, quote_asset, volume_bucket


def build_market_cap_buckets() -> List[BucketResult]:
    """Create nested cap folders under each volume bucket."""
    symbol_caps = fetch_market_caps()
    blacklist = read_blacklist()
    results: List[BucketResult] = []
    records: List[SymbolRecord] = []

    clean_existing_cap_files()
    clean_previous_reports()

    for volume_bucket in VOLUME_BUCKETS:
        source_dir = OUTPUT_DIR / f"vol_{volume_bucket}"
        if not source_dir.exists():
            continue

        for source_file in source_dir.glob("*.txt"):
            if "/cap_" in str(source_file).replace("\\", "/"):
                continue

            parts = source_file.stem.split("_")
            if len(parts) < 4:
                continue

            exchange, quote_asset, volume_bucket_label = parse_source_metadata(source_file)
            symbols = read_symbols(source_file)

            for cap_label, min_cap, max_cap in CAP_BUCKETS:
                filtered: List[str] = []
                for symbol in symbols:
                    base_symbol = extract_base_symbol(symbol, quote_asset)
                    if not base_symbol:
                        continue

                    if base_symbol.lower() in blacklist or symbol.lower() in blacklist:
                        continue

                    market_cap = symbol_caps.get(base_symbol.lower())
                    if market_cap is None:
                        continue

                    if matches_cap_bucket(market_cap, min_cap, max_cap):
                        filtered.append(symbol)
                        records.append(
                            SymbolRecord(
                                exchange=exchange,
                                quote_asset=quote_asset,
                                volume_bucket=volume_bucket_label,
                                source_file=source_file,
                                tv_symbol=symbol,
                                base_symbol=base_symbol,
                                market_cap=market_cap,
                                cap_bucket=cap_label,
                            )
                        )

                if not filtered:
                    continue

                cap_dir = source_dir / f"cap_{cap_label}"
                cap_dir.mkdir(parents=True, exist_ok=True)
                output_file = cap_dir / source_file.name
                unique_symbols = sorted(set(filtered))
                output_file.write_text(",\n".join(unique_symbols), encoding="utf-8")
                results.append(BucketResult(cap_label, output_file, len(unique_symbols)))

    if records:
        write_summary_reports(records, blacklist)
        write_exchange_rankings(records, blacklist)

    return results


def write_summary_reports(records: List[SymbolRecord], blacklist: set[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_DIR / "crypto_marketcap_summary.csv"
    md_path = OUTPUT_DIR / "crypto_marketcap_summary.md"

    csv_lines = [
        "exchange,quote_asset,volume_bucket,cap_bucket,symbol,base_symbol,market_cap,source_file"
    ]
    for record in sorted(records, key=lambda item: (item.exchange, item.quote_asset, item.volume_bucket, item.cap_bucket, item.tv_symbol)):
        csv_lines.append(
            f"{record.exchange},{record.quote_asset},{record.volume_bucket},{record.cap_bucket},{record.tv_symbol},{record.base_symbol},{int(record.market_cap)},{record.source_file.name}"
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    grouped: Dict[Tuple[str, str, str], int] = {}
    for record in records:
        key = (record.exchange, record.volume_bucket, record.cap_bucket)
        grouped[key] = grouped.get(key, 0) + 1

    lines = [
        "# Crypto Market Cap Summary",
        f"Generated on {datetime.now().strftime('%d-%b-%y').lower()}",
        "",
        f"Blacklisted symbols: {len(blacklist)}",
        "",
        "## Totals by Exchange / Volume / Cap",
    ]

    for exchange, volume_bucket, cap_bucket in sorted(grouped.keys()):
        lines.append(f"- {exchange} | {volume_bucket} | {cap_bucket}: {grouped[(exchange, volume_bucket, cap_bucket)]} symbols")

    lines.extend(["", "## Symbol List"])
    for record in sorted(records, key=lambda item: (item.exchange, item.volume_bucket, item.cap_bucket, item.tv_symbol)):
        lines.append(
            f"- {record.exchange} | {record.volume_bucket} | {record.cap_bucket} | {record.tv_symbol} | ${int(record.market_cap):,}"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_ranked_records(records: List[SymbolRecord]) -> List[RankedRecord]:
    ranked: List[RankedRecord] = []
    for record in records:
        rank_score = score_record(record.volume_bucket, record.cap_bucket)
        ranked.append(
            RankedRecord(
                exchange=record.exchange,
                symbol=record.tv_symbol,
                quote_asset=record.quote_asset,
                volume_bucket=record.volume_bucket,
                cap_bucket=record.cap_bucket,
                market_cap=record.market_cap,
                rank_score=rank_score,
                source_file=record.source_file,
            )
        )
    return ranked


def write_exchange_rankings(records: List[SymbolRecord], blacklist: set[str]) -> None:
    best_records: Dict[Tuple[str, str], RankedRecord] = {}
    for record in build_ranked_records(records):
        key = (record.exchange, record.symbol)
        current = best_records.get(key)
        if current is None or (record.rank_score, record.market_cap) > (current.rank_score, current.market_cap):
            best_records[key] = record

    ranked_records = list(best_records.values())
    csv_path = OUTPUT_DIR / "crypto_exchange_rankings.csv"
    md_path = OUTPUT_DIR / "crypto_exchange_rankings.md"
    rankings_dir = OUTPUT_DIR / "crypto_rankings"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    csv_lines = [
        "exchange,symbol,quote_asset,volume_bucket,cap_bucket,market_cap,rank_score,blacklisted,source_file"
    ]
    for record in sorted(
        ranked_records,
        key=lambda item: (item.exchange, -item.rank_score, -item.market_cap, item.symbol),
    ):
        base_symbol = extract_blacklist_key(record.symbol, record.quote_asset)
        is_blacklisted = "yes" if base_symbol.lower() in blacklist or record.symbol.lower() in blacklist else "no"
        csv_lines.append(
            f"{record.exchange},{record.symbol},{record.quote_asset},{record.volume_bucket},{record.cap_bucket},{int(record.market_cap)},{record.rank_score},{is_blacklisted},{record.source_file.name}"
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    lines = [
        "# Crypto Exchange Rankings",
        f"Generated on {datetime.now().strftime('%d-%b-%y').lower()}",
        "",
        "This list is sorted for beginners who want liquid coins with a better risk profile.",
        "Start with the 10M-100M market cap range and check the volume bucket first.",
        "Use the TXT files in output/crypto_rankings/ to import directly into TradingView.",
        f"Blacklisted symbols: {len(blacklist)}",
        "",
        "## How To Read This List",
        "- 10M-100M is the main target range.",
        "- 5M+ volume is best, 1M-5M is still acceptable.",
        "- ✅ means the symbol is not blacklisted.",
        "- Focus on the top entries in each exchange section.",
        "",
    ]

    by_exchange: Dict[str, List[RankedRecord]] = {}
    for record in ranked_records:
        by_exchange.setdefault(record.exchange, []).append(record)

    for exchange in sorted(by_exchange.keys()):
        exchange_records = sorted(
            by_exchange[exchange],
            key=lambda item: (-item.rank_score, -item.market_cap, item.symbol),
        )

        # Split spot vs perpetual
        spot_records = [r for r in exchange_records if not r.symbol.endswith('.P')]
        perp_records = [r for r in exchange_records if r.symbol.endswith('.P')]

        # --- SPOT section ---
        lines.append(f"## {exchange.upper()}")
        lines.append(f"Top SPOT candidates for {exchange.upper()}, sorted from strongest to weakest.")
        lines.append("| Rank | Symbol | Market Cap | Cap Range | Volume | Status |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for index, record in enumerate(spot_records[:20], start=1):
            base_symbol = extract_blacklist_key(record.symbol, record.quote_asset)
            is_blacklisted = base_symbol.lower() in blacklist or record.symbol.lower() in blacklist
            ethics_status = "❌ SKIP" if is_blacklisted else "✅ OK"
            lines.append(
                f"| {index} | {record.symbol} | ${int(record.market_cap):,} | {record.cap_bucket} | {record.volume_bucket} | {ethics_status} |"
            )
        lines.append("")

        # --- PERPETUAL section ---
        if perp_records:
            lines.append(f"### 🔮 {exchange.upper()} Perpetual Futures (.P)")
            lines.append(f"Top perpetual candidates for {exchange.upper()}.")
            lines.append("| Rank | Symbol | Market Cap | Cap Range | Volume | Status |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for index, record in enumerate(perp_records[:20], start=1):
                base_symbol = extract_blacklist_key(record.symbol, record.quote_asset)
                is_blacklisted = base_symbol.lower() in blacklist or record.symbol.lower() in blacklist
                ethics_status = "❌ SKIP" if is_blacklisted else "✅ OK"
                lines.append(
                    f"| {index} | {record.symbol} | ${int(record.market_cap):,} | {record.cap_bucket} | {record.volume_bucket} | {ethics_status} |"
                )
            lines.append("")

        # Generate per-exchange files (spot + perp)
        write_exchange_files(exchange, spot_records, perp_records, blacklist, rankings_dir)

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def create_master_watchlist() -> None:
    """Aggregate all per-exchange TradingView imports into master watchlist.
    
    Also pulls .P perpetual symbols directly from cap-bucket files so they
    are never missing from the combined watchlist.
    """
    rankings_dir = OUTPUT_DIR / "crypto_rankings"
    all_symbols: set[str] = set()
    file_count = 0

    # 1) Top-20 per-exchange files
    if rankings_dir.exists():
        for import_file in rankings_dir.glob("*/*tradingview_import.txt"):
            file_count += 1
            try:
                content = import_file.read_text(encoding="utf-8").strip()
                symbols = [s.strip().rstrip(",") for s in content.split("\n") if s.strip()]
                all_symbols.update(symbols)
            except Exception as e:
                print(f"  Warning: Could not read {import_file}: {e}")

    # 2) Direct .P perpetual entries from every cap bucket
    perp_count = 0
    for vol_bucket in VOLUME_BUCKETS:
        vol_dir = OUTPUT_DIR / f"vol_{vol_bucket}"
        if not vol_dir.exists():
            continue
        for cap_label, _, _ in CAP_BUCKETS:
            cap_dir = vol_dir / f"cap_{cap_label}"
            if not cap_dir.exists():
                continue
            for perp_file in cap_dir.glob("*_perp_pairs_*.txt"):
                try:
                    symbols = read_symbols(perp_file)
                    perp_count += 1
                    all_symbols.update(symbols)
                except Exception as e:
                    print(f"  Warning: Could not read {perp_file}: {e}")

    print(f"Found {file_count} exchange import files + {perp_count} perpetual files = {len(all_symbols)} total symbols")

    if all_symbols:
        master_path = OUTPUT_DIR / "tradingview_master_watchlist.txt"
        sorted_symbols = sorted(all_symbols)
        master_path.write_text("\n".join(sorted_symbols) + "\n", encoding="utf-8")
        print(f"✓ Master watchlist created: {len(sorted_symbols)} unique symbols")


def main() -> None:
    print("Creating market-cap buckets from current volume output...")
    results = build_market_cap_buckets()

    if not results:
        print("No market-cap bucket files were created.")
        return

    summary: Dict[str, int] = {}
    for result in results:
        summary[result.bucket_label] = summary.get(result.bucket_label, 0) + result.symbol_count

    print("Market-cap buckets created:")
    for bucket_label in sorted(summary.keys()):
        print(f"  {bucket_label}: {summary[bucket_label]} symbols")

    summary_csv = OUTPUT_DIR / "crypto_marketcap_summary.csv"
    summary_md = OUTPUT_DIR / "crypto_marketcap_summary.md"
    if summary_csv.exists() and summary_md.exists():
        print(f"Combined crypto summary written to {summary_csv} and {summary_md}")

    rankings_csv = OUTPUT_DIR / "crypto_exchange_rankings.csv"
    rankings_md = OUTPUT_DIR / "crypto_exchange_rankings.md"
    if rankings_csv.exists() and rankings_md.exists():
        print(f"Exchange rankings written to {rankings_csv} and {rankings_md}")
        print(f"Per-exchange files written to {OUTPUT_DIR}/crypto_rankings/")
    
    create_master_watchlist()


def write_exchange_files(exchange: str, spot_records: List[RankedRecord], perp_records: List[RankedRecord], blacklist: set[str], output_dir: Path) -> None:
    """Write per-exchange markdown and TradingView txt files, split spot vs perpetual."""
    exchange_dir = output_dir / exchange.lower()
    exchange_dir.mkdir(parents=True, exist_ok=True)

    # --- Combined Markdown (spot + perp) ---
    md_path = exchange_dir / f"{exchange}_top_20.md"
    md_lines = [
        f"# {exchange.upper()} - TradingView Shortlist",
        f"Generated on {datetime.now().strftime('%d-%b-%y').lower()}",
        "",
        "## 📊 SPOT",
        "",
        "| Rank | Symbol | Market Cap | Cap Range | Volume | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for index, record in enumerate(spot_records[:20], start=1):
        base_symbol = extract_blacklist_key(record.symbol, record.quote_asset)
        is_blacklisted = base_symbol.lower() in blacklist or record.symbol.lower() in blacklist
        ethics_status = "❌ SKIP" if is_blacklisted else "✅ OK"
        md_lines.append(
            f"| {index} | {record.symbol} | ${int(record.market_cap):,} | {record.cap_bucket} | {record.volume_bucket} | {ethics_status} |"
        )

    if perp_records:
        md_lines.extend(["", "## 🔮 PERPETUAL (.P)", "", "| Rank | Symbol | Market Cap | Cap Range | Volume | Status |", "| --- | --- | --- | --- | --- | --- |"])
        for index, record in enumerate(perp_records[:20], start=1):
            base_symbol = extract_blacklist_key(record.symbol, record.quote_asset)
            is_blacklisted = base_symbol.lower() in blacklist or record.symbol.lower() in blacklist
            ethics_status = "❌ SKIP" if is_blacklisted else "✅ OK"
            md_lines.append(
                f"| {index} | {record.symbol} | ${int(record.market_cap):,} | {record.cap_bucket} | {record.volume_bucket} | {ethics_status} |"
            )

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # --- TradingView import (spot + perp combined) ---
    txt_path = exchange_dir / f"{exchange}_tradingview_import.txt"
    txt_lines = [r.symbol for r in spot_records[:20]] + [r.symbol for r in perp_records[:20]]
    txt_path.write_text(",\n".join(txt_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
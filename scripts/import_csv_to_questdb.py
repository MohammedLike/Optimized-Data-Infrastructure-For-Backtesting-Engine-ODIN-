"""Resample sample 1m CSV to 5m and import into QuestDB."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

import polars as pl

from odin_data.config import settings
from odin_data.data_loader import DataLoader
from odin_data.questdb import QuestDBClient
from services.nightly_etl.export import csv_sample_range


def prepare_import_frame(symbol: str, timeframe: str, csv_path: Path) -> pl.DataFrame:
    frame = pl.read_csv(csv_path, try_parse_dates=True)
    if frame.is_empty() or "timestamp" not in frame.columns:
        raise SystemExit(f"No timestamps in CSV: {csv_path}")

    frame = (
        frame.filter(pl.col("symbol") == symbol)
        .with_columns(pl.col("timestamp").cast(pl.Datetime(time_unit="us", time_zone="UTC")))
        .sort("timestamp")
    )
    if frame.is_empty():
        raise SystemExit(f"No rows for symbol={symbol} in {csv_path}")

    if timeframe == "5m":
        frame = DataLoader._resample_to_5m(frame)

    return frame.with_columns(
        pl.lit(symbol).alias("symbol"),
        pl.lit(timeframe).alias("timeframe"),
    ).select(["symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume"])


def main() -> None:
    symbol = settings.default_symbol
    timeframe = settings.default_timeframe
    csv_path = settings.raw_csv_path
    if not csv_path.exists():
        raise SystemExit(f"Sample CSV not found: {csv_path}")

    client = QuestDBClient()
    if not client.ping():
        raise SystemExit(
            "QuestDB is not reachable. Start it with:\n"
            "  docker compose -f infra/docker-compose.yml up -d questdb"
        )

    start, end = csv_sample_range()
    print(f"Preparing {symbol} {timeframe} from {csv_path.name}")
    print(f"  Range: {start.isoformat()} -> {end.isoformat()}")

    frame = prepare_import_frame(symbol, timeframe, csv_path)
    print(f"  Resampled rows: {frame.height}")

    client.ensure_table(recreate=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as tmp:
        tmp_path = Path(tmp.name)
        frame.write_csv(tmp_path)

    try:
        client.import_csv_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    count = client.row_count(symbol=symbol, timeframe=timeframe)
    print(f"Imported {count} rows into QuestDB table '{client.table}'")


if __name__ == "__main__":
    main()

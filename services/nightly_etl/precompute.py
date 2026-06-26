"""Precompute Tier A indicators into Parquet."""

from datetime import datetime, timezone

import polars as pl

from odin_data.config import settings
from odin_data.parquet_store import ParquetStore
from odin_indicators.compute import precompute_all


def precompute_nifty_5m() -> None:
    symbol = settings.default_symbol
    timeframe = settings.default_timeframe
    store = ParquetStore()
    catalog = store.catalog.get_range(symbol, timeframe)
    if catalog[0] is None or catalog[1] is None:
        print("No OHLC catalog found. Run export first.")
        return

    start, end = catalog
    ohlc = store.read_ohlc(symbol, timeframe, start, end)
    if ohlc is None or ohlc.is_empty():
        print("No OHLC data to precompute.")
        return

    indicators = precompute_all(ohlc)
    merged = ohlc.join(indicators, on="timestamp", how="left")
    merged = merged.with_columns(pl.col("timestamp").dt.strftime("%Y-%m").alias("month"))

    for month in merged["month"].unique().sort():
        month_df = merged.filter(pl.col("month") == month).drop("month")
        path = store.write_indicator_month(symbol, timeframe, month, month_df)
        print(f"Wrote indicators {path}")

    print(f"Precompute complete: {merged.height} rows, {len(merged.columns)} columns")


if __name__ == "__main__":
    precompute_nifty_5m()

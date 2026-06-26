from datetime import datetime

import polars as pl
from pydantic import BaseModel, Field


OHLC_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class OHLCBar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class DataRequest(BaseModel):
    symbol: str = "NIFTY"
    timeframe: str = "5m"
    series: str = "spot"
    start: datetime
    end: datetime


def empty_ohlc_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Float64,
        }
    )


def validate_ohlc(df: pl.DataFrame) -> pl.DataFrame:
    missing = [c for c in OHLC_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"OHLC frame missing columns: {missing}")
    return df.select(OHLC_COLUMNS).sort("timestamp")

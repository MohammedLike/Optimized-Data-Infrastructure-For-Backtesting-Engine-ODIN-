from pathlib import Path
from typing import Any

import polars as pl
import yaml

REGISTRY_PATH = Path(__file__).parent / "registry.yaml"


def load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["indicators"]


def compute_ema(frame: pl.DataFrame, span: int) -> pl.Series:
    return frame.select(pl.col("close").ewm_mean(span=span)).to_series()


def compute_sma(frame: pl.DataFrame, window: int) -> pl.Series:
    return frame.select(pl.col("close").rolling_mean(window)).to_series()


def compute_rsi(frame: pl.DataFrame, period: int = 14) -> pl.Series:
    delta = frame["close"].diff()
    gain = delta.clip(lower_bound=0)
    loss = (-delta).clip(lower_bound=0)
    avg_gain = gain.ewm_mean(alpha=1 / period)
    avg_loss = loss.ewm_mean(alpha=1 / period)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_atr(frame: pl.DataFrame, period: int = 14) -> pl.Series:
    prev_close = frame["close"].shift(1)
    tr = pl.max_horizontal(
        frame["high"] - frame["low"],
        (frame["high"] - prev_close).abs(),
        (frame["low"] - prev_close).abs(),
    )
    return tr.ewm_mean(alpha=1 / period)


def compute_bollinger(frame: pl.DataFrame, window: int, std: float, band: str) -> pl.Series:
    mid = frame["close"].rolling_mean(window)
    dev = frame["close"].rolling_std(window) * std
    if band == "upper":
        return mid + dev
    return mid - dev


def compute_macd(frame: pl.DataFrame, fast: int, slow: int, signal: int, component: str) -> pl.Series:
    ema_fast = frame["close"].ewm_mean(span=fast)
    ema_slow = frame["close"].ewm_mean(span=slow)
    line = ema_fast - ema_slow
    if component == "signal":
        return line.ewm_mean(span=signal)
    return line


def compute_indicator(frame: pl.DataFrame, name: str, params: dict[str, Any] | None = None) -> pl.Series:
    registry = load_registry()
    if name not in registry:
        raise KeyError(f"Unknown indicator: {name}")
    spec = registry[name]
    if "column" in spec:
        return frame[spec["column"]]
    params = {**spec.get("params", {}), **(params or {})}
    fn = spec["function"]
    if fn == "ema":
        return compute_ema(frame, params["span"])
    if fn == "sma":
        return compute_sma(frame, params["window"])
    if fn == "rsi":
        return compute_rsi(frame, params.get("period", 14))
    if fn == "atr":
        return compute_atr(frame, params.get("period", 14))
    if fn == "bollinger":
        return compute_bollinger(frame, params["window"], params["std"], params["band"])
    if fn == "macd":
        return compute_macd(frame, params["fast"], params["slow"], params["signal"], params["component"])
    raise ValueError(f"Unsupported indicator function: {fn}")


def precompute_all(frame: pl.DataFrame) -> pl.DataFrame:
    registry = load_registry()
    result = frame.select("timestamp")
    for name, spec in registry.items():
        if not spec.get("precompute"):
            continue
        try:
            result = result.with_columns(compute_indicator(frame, name).alias(name))
        except Exception:
            continue
    return result

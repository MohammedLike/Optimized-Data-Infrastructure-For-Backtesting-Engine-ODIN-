"""Baseline slow path: Pandas full load + inline RSI — reproduces pre-ODIN latency."""

import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from odin_data.config import settings


def compute_rsi_pandas(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def run_baseline() -> dict:
    path = settings.raw_csv_path
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    df = pd.read_csv(path)
    timings["csv_load_ms"] = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    df = df[df["symbol"] == "NIFTY"].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").resample("5min").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna().reset_index()
    timings["resample_5m_ms"] = (time.perf_counter() - t1) * 1000

    t2 = time.perf_counter()
    df["rsi_14"] = compute_rsi_pandas(df["close"])
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    timings["indicator_compute_ms"] = (time.perf_counter() - t2) * 1000

    t3 = time.perf_counter()
    signals = (df["close"] > df["ema_20"]) & (df["rsi_14"] > 50)
    entries = 0
    for i in range(1, len(df)):
        if signals.iloc[i] and not signals.iloc[i - 1]:
            entries += 1
    timings["python_loop_ms"] = (time.perf_counter() - t3) * 1000
    timings["total_ms"] = sum(timings.values())

    result = {
        "path": "baseline_pandas",
        "rows": len(df),
        "entries": entries,
        "timings": {k: round(v, 2) for k, v in timings.items()},
        "timeout_risk": timings["total_ms"] > settings.gateway_timeout_seconds * 1000,
        "root_causes": [
            "Full CSV/SQL load on every request",
            "Indicators recomputed per run",
            "Single-threaded Python condition loop",
        ],
    }
    out = ROOT / "benchmarks" / "results"
    out.mkdir(parents=True, exist_ok=True)
    out_file = out / "baseline.json"
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run_baseline()

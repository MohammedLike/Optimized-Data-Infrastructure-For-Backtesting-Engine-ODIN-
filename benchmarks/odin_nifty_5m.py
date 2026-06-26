"""ODIN fast path benchmark: Parquet + Polars + Numba for NIFTY 5m."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from odin_data.prewarm import prewarm_defaults, warmup_backtest
from odin_engine.backtest import BacktestEngine, BacktestRequest
from odin_engine.conditions import Condition, Operator


def run_odin_benchmark() -> dict:
    request = BacktestRequest(
        symbol="NIFTY",
        timeframe="5m",
        entry_rules=[
            Condition(left_indicator="current_close", operator=Operator.GT, right_indicator="ema_20"),
            Condition(left_indicator="rsi_14", operator=Operator.GT, right_value=50),
        ],
    )

    # Simulate API startup: RAM prewarm + one throwaway backtest (JIT compile)
    prewarm_defaults()
    warmup_backtest()
    engine = BacktestEngine()

    t0 = time.perf_counter()
    cold = engine.run(request)
    cold_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    warm = engine.run(request)
    warm_ms = (time.perf_counter() - t1) * 1000

    result = {
        "path": "odin",
        "cold": {
            "data_tier": cold.data_tier,
            "total_trades": cold.total_trades,
            "latency_ms": cold.latency_ms,
            "wall_ms": round(cold_ms, 2),
        },
        "warm": {
            "data_tier": warm.data_tier,
            "total_trades": warm.total_trades,
            "latency_ms": warm.latency_ms,
            "wall_ms": round(warm_ms, 2),
        },
        "targets_met": {
            "cold_under_1s": cold_ms < 1000,
            "cold_under_5s": cold_ms < 5000,
            "warm_under_500ms": warm_ms < 500,
        },
    }

    out = ROOT / "benchmarks" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "odin_nifty_5m.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    run_odin_benchmark()

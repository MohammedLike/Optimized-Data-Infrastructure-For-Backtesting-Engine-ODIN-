import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))


def test_imports():
    from odin_data import DataLoader, ParquetStore
    from odin_engine import BacktestEngine
    from odin_indicators import IndicatorResolver

    assert DataLoader is not None
    assert ParquetStore is not None
    assert BacktestEngine is not None
    assert IndicatorResolver is not None


def test_backtest_runs():
    from odin_engine.backtest import BacktestEngine, BacktestRequest

    engine = BacktestEngine()
    result = engine.run(BacktestRequest(symbol="NIFTY", timeframe="5m"))
    assert result.symbol == "NIFTY"
    assert "data" in result.latency_ms

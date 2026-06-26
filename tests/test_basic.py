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


def test_strykex_catalog():
    from odin_indicators.strykex_catalog import indicator_count, load_catalog, rule_count

    catalog = load_catalog()
    assert indicator_count() == 96
    assert rule_count() > 200
    assert any(i["slug"] == "rsi" for i in catalog)
    rsi = next(i for i in catalog if i["slug"] == "rsi")
    purposes = {r["purpose"] for r in rsi["rules"]}
    assert "entry_long" in purposes
    assert "exit_long" in purposes

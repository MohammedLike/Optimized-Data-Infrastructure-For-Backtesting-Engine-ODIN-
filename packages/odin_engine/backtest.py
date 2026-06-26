import time
from datetime import datetime
from typing import Any

import numpy as np
import polars as pl
from pydantic import BaseModel, Field

from odin_data.data_loader import DataLoader
from odin_data.redis_cache import RedisCache
from odin_engine.conditions import Condition, Operator, RuleSet
from odin_engine.kernel import run_backtest_kernel
from odin_indicators.resolver import IndicatorResolver


class BacktestRequest(BaseModel):
    symbol: str = "NIFTY"
    timeframe: str = "5m"
    series: str = "spot"
    start: datetime | None = None
    end: datetime | None = None
    entry_rules: list[Condition] = Field(default_factory=list)
    exit_rules: list[Condition] = Field(default_factory=list)
    initial_capital: float = 100_000.0


class Trade(BaseModel):
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float


class BacktestResult(BaseModel):
    symbol: str
    timeframe: str
    total_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    max_drawdown_pct: float
    trades: list[Trade]
    equity_curve: list[dict[str, Any]]
    latency_ms: dict[str, float]
    data_tier: str


OP_MAP = {
    Operator.EQ: 0,
    Operator.GT: 1,
    Operator.LT: 2,
    Operator.GTE: 3,
    Operator.LTE: 4,
    Operator.CROSSES_ABOVE: 1,
    Operator.CROSSES_BELOW: 2,
}


class BacktestEngine:
    def __init__(self, loader: DataLoader | None = None) -> None:
        self.loader = loader or DataLoader()

    def run(self, request: BacktestRequest) -> BacktestResult:
        t0 = time.perf_counter()
        start, end = request.start, request.end
        if start is None or end is None:
            start, end = self.loader.default_range()

        ohlc, load_stats = self.loader.load_ohlc(request.symbol, request.timeframe, start, end)
        t_data = time.perf_counter()

        if ohlc.is_empty():
            return BacktestResult(
                symbol=request.symbol,
                timeframe=request.timeframe,
                total_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                total_pnl_pct=0.0,
                max_drawdown_pct=0.0,
                trades=[],
                equity_curve=[],
                latency_ms={"data": 0, "indicators": 0, "engine": 0, "total": 0},
                data_tier=load_stats.tier,
            )

        precomputed = self.loader.parquet.read_indicators(request.symbol, request.timeframe, start, end)
        resolver = IndicatorResolver(self.loader.redis, request.symbol, request.timeframe)

        entry_rules = request.entry_rules or [
            Condition(left_indicator="current_close", operator=Operator.GT, right_indicator="ema_20")
        ]

        left_cols = []
        right_cols = []
        op_codes = []
        n = ohlc.height
        for rule in entry_rules:
            left = self._aligned_series(resolver, rule.left_indicator, ohlc, start, end, precomputed, n)
            if rule.right_indicator:
                right = self._aligned_series(resolver, rule.right_indicator, ohlc, start, end, precomputed, n)
            else:
                right = np.full(n, rule.right_value or 0.0)
            left_cols.append(left)
            right_cols.append(right)
            op_codes.append(OP_MAP[rule.operator])

        t_ind = time.perf_counter()

        left_arr = np.vstack(left_cols)
        right_arr = np.vstack(right_cols)
        op_arr = np.array(op_codes, dtype=np.int64)
        close = ohlc["close"].to_numpy()

        entries, exits, positions = run_backtest_kernel(left_arr, right_arr, op_arr, close)
        t_engine = time.perf_counter()

        trades = self._build_trades(ohlc, entries, exits)
        equity = self._build_equity(ohlc, positions, request.initial_capital)
        total_pnl = sum(t.pnl for t in trades)
        wins = sum(1 for t in trades if t.pnl > 0)
        win_rate = (wins / len(trades) * 100.0) if trades else 0.0
        max_dd = self._max_drawdown(equity)

        return BacktestResult(
            symbol=request.symbol,
            timeframe=request.timeframe,
            total_trades=len(trades),
            win_rate=round(win_rate, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl / request.initial_capital * 100, 2),
            max_drawdown_pct=round(max_dd, 2),
            trades=trades,
            equity_curve=equity,
            latency_ms={
                "data": round((t_data - t0) * 1000, 2),
                "indicators": round((t_ind - t_data) * 1000, 2),
                "engine": round((t_engine - t_ind) * 1000, 2),
                "total": round((t_engine - t0) * 1000, 2),
            },
            data_tier=load_stats.tier,
        )

    def _aligned_series(
        self,
        resolver: IndicatorResolver,
        name: str,
        ohlc: pl.DataFrame,
        start: datetime,
        end: datetime,
        precomputed: pl.DataFrame | None,
        length: int,
    ) -> np.ndarray:
        series = resolver.resolve(name, ohlc, start, end, precomputed)
        return series.to_numpy()

    @staticmethod
    def _build_trades(ohlc: pl.DataFrame, entries: np.ndarray, exits: np.ndarray) -> list[Trade]:
        trades: list[Trade] = []
        entry_idx = None
        timestamps = ohlc["timestamp"].to_list()
        closes = ohlc["close"].to_numpy()
        for i in range(len(closes)):
            if entries[i]:
                entry_idx = i
            if exits[i] and entry_idx is not None:
                entry_price = float(closes[entry_idx])
                exit_price = float(closes[i])
                pnl = exit_price - entry_price
                trades.append(
                    Trade(
                        entry_time=timestamps[entry_idx],
                        exit_time=timestamps[i],
                        entry_price=entry_price,
                        exit_price=exit_price,
                        pnl=round(pnl, 2),
                        pnl_pct=round(pnl / entry_price * 100, 4),
                    )
                )
                entry_idx = None
        return trades

    @staticmethod
    def _build_equity(ohlc: pl.DataFrame, positions: np.ndarray, capital: float) -> list[dict[str, Any]]:
        equity = []
        cash = capital
        shares = 0.0
        closes = ohlc["close"].to_numpy()
        timestamps = ohlc["timestamp"].to_list()
        for i, close in enumerate(closes):
            if i > 0 and positions[i] == 1 and positions[i - 1] == 0:
                shares = cash / close
                cash = 0.0
            elif i > 0 and positions[i] == 0 and positions[i - 1] == 1:
                cash = shares * close
                shares = 0.0
            value = cash + shares * close
            equity.append({"timestamp": timestamps[i].isoformat(), "equity": round(float(value), 2)})
        return equity

    @staticmethod
    def _max_drawdown(equity: list[dict[str, Any]]) -> float:
        if not equity:
            return 0.0
        values = [point["equity"] for point in equity]
        peak = values[0]
        max_dd = 0.0
        for value in values:
            peak = max(peak, value)
            dd = (peak - value) / peak * 100 if peak else 0.0
            max_dd = max(max_dd, dd)
        return max_dd

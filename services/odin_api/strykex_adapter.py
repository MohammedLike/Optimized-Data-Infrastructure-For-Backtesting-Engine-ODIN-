from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from odin_data.data_loader import DataLoader
from odin_engine.backtest import BacktestResult
from odin_engine.conditions import Condition, Operator


class StrykeXRule(BaseModel):
    parameter: str
    condition: str
    value: float | None = None
    compare_parameter: str | None = None
    timeframe: str = "5m"


class StrykeXBacktestRequest(BaseModel):
    """Mirrors StrykeX Strategy Builder preview/backtest payload (subset)."""
    name: str = "strategy"
    symbol: str = "NIFTY"
    segment: str = "Options"
    chart_type: str = "Candlestick"
    timeframe: str = "5m"
    chart_selection: str = "Spot"
    strategy_type: str = "Price Action"
    trade_direction: str = "Bullish"
    entry_rules: list[StrykeXRule] = Field(default_factory=list)
    exit_rules: list[StrykeXRule] = Field(default_factory=list)
    start: datetime | None = None
    end: datetime | None = None
    use_odin: bool = True


CONDITION_MAP = {
    "equal": Operator.EQ,
    "eq": Operator.EQ,
    "greater_than": Operator.GT,
    "gt": Operator.GT,
    "less_than": Operator.LT,
    "lt": Operator.LT,
    "crosses_above": Operator.CROSSES_ABOVE,
    "crosses_below": Operator.CROSSES_BELOW,
}

PARAMETER_MAP = {
    "current close": "current_close",
    "current_close": "current_close",
    "close": "close",
    "ema 20": "ema_20",
    "ema_9": "ema_9",
    "ema 9": "ema_9",
    "rsi": "rsi_14",
    "rsi 14": "rsi_14",
}


def _map_parameter(name: str) -> str:
    key = name.lower().strip()
    return PARAMETER_MAP.get(key, key.replace(" ", "_"))


def _map_rules(rules: list[StrykeXRule]) -> list[Condition]:
    mapped: list[Condition] = []
    for index, rule in enumerate(rules):
        op = CONDITION_MAP.get(rule.condition.lower().replace(" ", "_"), Operator.GT)
        mapped.append(
            Condition(
                left_indicator=_map_parameter(rule.parameter),
                operator=op,
                right_value=rule.value,
                right_indicator=_map_parameter(rule.compare_parameter) if rule.compare_parameter else None,
                case_id=index + 1,
            )
        )
    return mapped


def to_backtest_request(request: StrykeXBacktestRequest):
    from odin_engine.backtest import BacktestRequest

    start, end = request.start, request.end
    if start is None or end is None:
        start, end = DataLoader.default_range(days=365)

    entry_rules = _map_rules(request.entry_rules)
    if not entry_rules:
        entry_rules = [Condition(left_indicator="current_close", operator=Operator.GT, right_indicator="ema_20")]

    return BacktestRequest(
        symbol=request.symbol,
        timeframe=request.timeframe,
        series=request.chart_selection.lower(),
        start=start,
        end=end,
        entry_rules=entry_rules,
        exit_rules=_map_rules(request.exit_rules),
    )


def to_strykex_response(result: BacktestResult) -> dict[str, Any]:
    return {
        "success": True,
        "engine": "odin",
        "summary": {
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "total_trades": result.total_trades,
            "win_rate": result.win_rate,
            "total_pnl": result.total_pnl,
            "total_pnl_pct": result.total_pnl_pct,
            "max_drawdown_pct": result.max_drawdown_pct,
        },
        "trades": [trade.model_dump() for trade in result.trades],
        "equity_curve": result.equity_curve,
        "latency": result.latency_ms,
        "data_tier": result.data_tier,
    }

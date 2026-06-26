import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from odin_engine.backtest import BacktestEngine, BacktestRequest, BacktestResult
from odin_engine.conditions import Condition
from services.odin_api.strykex_adapter import StrykeXBacktestRequest, to_backtest_request, to_strykex_response

app = FastAPI(title="ODIN Backtest API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = BacktestEngine()
_metrics: dict[str, Any] = {
    "requests": 0,
    "cache_hits": 0,
    "total_latency_ms": 0.0,
    "last_data_tier": None,
}


class GridBacktestRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["NIFTY"])
    timeframe: str = "5m"
    entry_rules: list[Condition] = Field(default_factory=list)
    param_grid: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "odin-api"}


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    avg_latency = (
        _metrics["total_latency_ms"] / _metrics["requests"] if _metrics["requests"] else 0.0
    )
    return {
        **_metrics,
        "avg_latency_ms": round(avg_latency, 2),
        "cache_hit_rate": round(
            _metrics["cache_hits"] / _metrics["requests"] * 100, 2
        )
        if _metrics["requests"]
        else 0.0,
    }


@app.post("/v1/backtest", response_model=BacktestResult)
def run_backtest(request: BacktestRequest) -> BacktestResult:
    t0 = time.perf_counter()
    result = engine.run(request)
    _record_metrics(result, t0)
    return result


@app.post("/v1/backtest/strykex")
def run_strykex_backtest(request: StrykeXBacktestRequest) -> dict[str, Any]:
    """Drop-in adapter for StrykeX Strategy Builder backtest calls."""
    t0 = time.perf_counter()
    try:
        odin_request = to_backtest_request(request)
        result = engine.run(odin_request)
        _record_metrics(result, t0)
        return to_strykex_response(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/backtest/grid")
def run_grid_backtest(request: GridBacktestRequest) -> dict[str, Any]:
    import ray

    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True, num_cpus=4)

    @ray.remote
    def _run(symbol: str, params: dict[str, Any]) -> dict[str, Any]:
        entry_rules = request.entry_rules
        if params.get("entry_rules"):
            entry_rules = [Condition(**c) for c in params["entry_rules"]]
        req = BacktestRequest(symbol=symbol, timeframe=request.timeframe, entry_rules=entry_rules)
        res = BacktestEngine().run(req)
        return {"symbol": symbol, "params": params, "result": res.model_dump()}

    futures = []
    grid = request.param_grid or [{}]
    for symbol in request.symbols:
        for params in grid:
            futures.append(_run.remote(symbol, params))

    results = ray.get(futures)
    return {"count": len(results), "results": results}


def _record_metrics(result: BacktestResult, t0: float) -> None:
    _metrics["requests"] += 1
    if result.data_tier == "redis":
        _metrics["cache_hits"] += 1
    _metrics["total_latency_ms"] += (time.perf_counter() - t0) * 1000
    _metrics["last_data_tier"] = result.data_tier

# StrykeX Integration

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/backtest` | Native ODIN backtest request |
| `POST /v1/backtest/strykex` | StrykeX adapter (drop-in) |
| `POST /v1/backtest/grid` | Multi-symbol/param Ray grid |
| `GET /metrics` | Latency and cache hit rate |

## StrykeX request example

```json
{
  "name": "test",
  "symbol": "NIFTY",
  "timeframe": "5m",
  "chart_selection": "Spot",
  "entry_rules": [
    {
      "parameter": "Current Close",
      "condition": "greater_than",
      "compare_parameter": "ema 20"
    }
  ],
  "use_odin": true
}
```

## Integration (Phase 5)

Set `USE_ODIN=true` in StrykeX backend and forward backtest calls to:

```
POST http://odin-api:8000/v1/backtest/strykex
```

(Inside Docker network port is 8000; on host use `http://localhost:47100`.)

Response includes `summary`, `trades`, `equity_curve`, `latency`, and `data_tier`.

## Timeout root cause

| Stage | Issue | ODIN fix |
|-------|-------|----------|
| Data fetch | Full history from QuestDB | Bounded query + Parquet |
| Indicators | Recomputed every run | Nightly precompute + Redis |
| Engine | Python loop | Numba JIT kernel |
| Gateway | 60s timeout | Total path under 10s |

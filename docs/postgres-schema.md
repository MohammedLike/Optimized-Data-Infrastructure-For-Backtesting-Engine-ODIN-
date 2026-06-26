# PostgreSQL Schema (ODIN)

PostgreSQL is ODIN's **persistent, queryable store** for backtest data. QuestDB remains the upstream time-series source; Redis and Parquet stay as hot/warm caches.

## Why PostgreSQL

| Store | Role |
|-------|------|
| **QuestDB** | Production OHLC source (time-series optimized) |
| **PostgreSQL** | Structured store you can query, extend, and inspect |
| **Parquet** | Fast columnar reads on disk |
| **Redis** | Sub-millisecond slice cache |

PostgreSQL fits well because you can add tables/columns later, run SQL analytics, and load NIFTY data from QuestDB in one place.

## Tables (`odin` schema)

### 1. `odin.ohlc_bars` — QuestDB OHLC

| Column | Type | Notes |
|--------|------|-------|
| symbol | VARCHAR | e.g. `NIFTY` |
| timeframe | VARCHAR | e.g. `5m` |
| series | VARCHAR | e.g. `spot` |
| ts | TIMESTAMPTZ | bar timestamp |
| open, high, low, close | DOUBLE | OHLC |
| volume | BIGINT | |
| source | VARCHAR | `questdb`, `csv`, etc. |

### 2. `odin.indicator_bars` — precomputed indicators

Wide table with Tier A columns from `registry.yaml`:

`ema_9`, `ema_20`, `ema_50`, `ema_200`, `sma_20`, `sma_50`, `rsi_14`, `atr_14`, `bb_upper_20`, `bb_lower_20`, `macd_line`, `macd_signal`

### 3. `odin.bar_extensions` — your future data

| Column | Type | Notes |
|--------|------|-------|
| payload | JSONB | Any extra fields you provide later |

New keys merge into existing JSON on upsert (`payload || EXCLUDED.payload`).

### View: `odin.market_bars`

Joins OHLC + indicators + extensions for one-query backtests.

## Quick start

```bash
# Start PostgreSQL
docker compose -f infra/docker-compose.yml up -d postgres

# Install dependency
pip install -e .

# Apply schema (also auto-runs on first docker start)
python scripts/init_database.py

# Load NIFTY data from existing Parquet seed
python scripts/seed_data.py
python scripts/sync_postgres.py

# Or load directly from QuestDB
USE_QUESTDB=true python scripts/sync_postgres.py
```

Enable reads in the backtest path:

```bash
USE_POSTGRES=true
```

Read tier order: **Redis → PostgreSQL → Parquet → QuestDB → CSV**

## Indicator catalog

StrykeX indicator metadata and entry/exit rules:

- `odin.indicator_catalog` — 96 indicators
- `odin.condition_rule_templates` — quant rule templates

See `docs/indicator-catalog.md` and run `python scripts/seed_indicator_catalog.py`.

## Example queries

```sql
-- Latest NIFTY 5m bars with RSI
SELECT ts, close, rsi_14
FROM odin.market_bars
WHERE symbol = 'NIFTY' AND timeframe = '5m'
ORDER BY ts DESC
LIMIT 20;

-- Add custom extension data (Python API or SQL)
INSERT INTO odin.bar_extensions (symbol, timeframe, ts, payload)
VALUES ('NIFTY', '5m', '2026-06-01T09:15:00Z', '{"vwap": 24510.5}');
```

## Environment

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://odin:odin@localhost:47132/odin` |
| `USE_POSTGRES` | `false` |

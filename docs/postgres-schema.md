# PostgreSQL Schema (ODIN)

PostgreSQL stores **indicator bars**, **indicator catalog**, and **extensible bar metadata**. OHLC lives in **QuestDB** (see `docs/questdb-schema.md`).

## Why PostgreSQL

| Store | Role |
|-------|------|
| **QuestDB** | OHLC source of truth (time-series optimized) |
| **PostgreSQL** | Indicators, catalog, extensions — structured SQL store |
| **Parquet** | Fast columnar reads on disk (OHLC + indicators) |
| **Redis** | Sub-millisecond slice cache |

## Tables (`odin` schema)

### 1. `odin.indicator_bars` — precomputed indicators

Wide table with Tier A columns from `registry.yaml`:

`ema_9`, `ema_20`, `ema_50`, `ema_200`, `sma_20`, `sma_50`, `rsi_14`, `atr_14`, `bb_upper_20`, `bb_lower_20`, `macd_line`, `macd_signal`

### 2. `odin.bar_extensions` — custom per-bar data

| Column | Type | Notes |
|--------|------|-------|
| payload | JSONB | Any extra fields you provide later |

New keys merge into existing JSON on upsert (`payload || EXCLUDED.payload`).

### 3. `odin.indicator_catalog` + `odin.condition_rule_templates`

96 StrykeX indicators and entry/exit rule templates. See `docs/indicator-catalog.md`.

### Legacy: `odin.ohlc_bars`

Schema remains for compatibility but **is not populated** in the QuestDB-first architecture. Use `scripts/sync_postgres.py` (indicators only) — it does not write OHLC.

### View: `odin.market_bars`

Joins `ohlc_bars` + indicators + extensions. Requires OHLC in PostgreSQL to be useful; with QuestDB-only OHLC, query indicators directly or join in application code.

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d questdb postgres

pip install -e .

python scripts/init_database.py
python scripts/setup_questdb_pipeline.py   # QuestDB + Parquet + indicators → PG

# Indicators only (after export + precompute)
python scripts/sync_postgres.py
python scripts/seed_indicator_catalog.py
```

## Example queries

```sql
-- Latest NIFTY 5m indicators
SELECT ts, rsi_14, ema_20, macd_line
FROM odin.indicator_bars
WHERE symbol = 'NIFTY' AND timeframe = '5m'
ORDER BY ts DESC
LIMIT 20;

-- Custom extension data
INSERT INTO odin.bar_extensions (symbol, timeframe, ts, payload)
VALUES ('NIFTY', '5m', '2026-06-01T09:15:00Z', '{"vwap": 24510.5}');
```

## Environment

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://odin:odin@localhost:47132/odin` |
| `USE_POSTGRES` | `true` |

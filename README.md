# Project ODIN

Optimized Data Infrastructure for NSE — backend acceleration layer for StrykeX Strategy Builder backtests.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python scripts/load_sample_data.py
python benchmarks/baseline_strykex.py

# Optional: PostgreSQL persistent store
docker compose -f infra/docker-compose.yml up -d postgres
python scripts/init_database.py
python scripts/sync_postgres.py

uvicorn services.odin_api.main:app --reload --app-dir .
```

## Services

- **ODIN API** — `POST /v1/backtest`, `POST /v1/backtest/grid`, `GET /metrics`
- **PostgreSQL** — `odin.ohlc_bars`, `odin.indicator_bars`, `odin.bar_extensions` (see `docs/postgres-schema.md`)
- **Nightly ETL** — `python -m services.nightly_etl.export` then `python -m services.nightly_etl.precompute`

## Scope (Phase 1)

NIFTY + 5-minute timeframe. QuestDB is source of truth; Parquet + Redis + PostgreSQL accelerate reads.

## Indicator catalog

96 StrykeX indicators with entry/exit rule templates — see `docs/indicator-catalog.md`.

```bash
python scripts/seed_indicator_catalog.py
```

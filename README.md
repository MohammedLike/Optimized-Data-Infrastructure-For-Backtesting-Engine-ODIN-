# Project ODIN

Optimized Data Infrastructure for NSE — backend acceleration layer for StrykeX Strategy Builder backtests.

## Architecture

```
OHLC:     QuestDB → Parquet → Redis → backtest
Other:    PostgreSQL (indicators, catalog, extensions)
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# Start data stores
docker compose -f infra/docker-compose.yml up -d questdb postgres redis

# Load sample CSV into QuestDB + Parquet + PostgreSQL indicators
python scripts/setup_questdb_pipeline.py

python benchmarks/baseline_strykex.py
python benchmarks/odin_nifty_5m.py

uvicorn services.odin_api.main:app --reload --app-dir .
```

## Services

- **QuestDB** — OHLC source of truth (Docker: port **47900**) — `docs/questdb-schema.md`
- **PostgreSQL** — indicators + catalog (Docker: port **47132**) — `docs/postgres-schema.md`
- **Redis** — cache (Docker: port **47179**)
- **ODIN API** — `POST /v1/backtest`, `GET /v1/indicators` (Docker: port **47100**)
- **Nightly ETL** — `python -m services.nightly_etl.export` then `precompute` then `scripts/sync_postgres.py`

## Scope (Phase 1)

NIFTY + 5-minute timeframe.

## Indicator catalog

96 StrykeX indicators with entry/exit rule templates — see `docs/indicator-catalog.md`.

```bash
python scripts/seed_indicator_catalog.py
```

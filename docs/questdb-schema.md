# QuestDB Schema (ODIN)

QuestDB is ODIN's **source of truth for OHLC** time-series data. Parquet and Redis cache reads; PostgreSQL stores indicators and catalog metadata only.

## Table: `ohlc_5m`

| Column | Type | Notes |
|--------|------|-------|
| symbol | SYMBOL | e.g. `NIFTY` |
| timeframe | SYMBOL | e.g. `5m` |
| timestamp | TIMESTAMP | bar open time (partition key) |
| open, high, low, close | DOUBLE | OHLC |
| volume | LONG | bar volume |

Partitioned by month on `timestamp`.

DDL (created by `QuestDBClient.ensure_table()`):

```sql
CREATE TABLE ohlc_5m (
    symbol SYMBOL,
    timeframe SYMBOL,
    timestamp TIMESTAMP,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY MONTH;
```

## Read tier order (OHLC)

**Redis → Parquet → QuestDB → CSV fallback**

PostgreSQL is **not** in the OHLC read path.

## Import sample data

```bash
# Start QuestDB (host port 47900)
docker compose -f infra/docker-compose.yml up -d questdb

# Full pipeline: CSV → QuestDB → Parquet → indicators → PostgreSQL
python scripts/setup_questdb_pipeline.py

# Or import QuestDB only
python scripts/import_csv_to_questdb.py
```

The sample CSV (`questdb-query-1781940224994.csv`) is 1-minute data; the import script resamples to 5-minute bars before loading.

## Query examples

```sql
-- Row count
SELECT count() FROM ohlc_5m WHERE symbol = 'NIFTY' AND timeframe = '5m';

-- Latest bars
SELECT timestamp, open, high, low, close, volume
FROM ohlc_5m
WHERE symbol = 'NIFTY' AND timeframe = '5m'
ORDER BY timestamp DESC
LIMIT 10;
```

Web console: http://localhost:47900 (when Docker is running).

## Environment

| Variable | Default (host) | Docker internal |
|----------|----------------|-----------------|
| `QUESTDB_HOST` | `localhost` | `odin-questdb` |
| `QUESTDB_PORT` | `47900` | `9000` |
| `QUESTDB_TABLE` | `ohlc_5m` | |
| `USE_QUESTDB` | `true` | |

## Nightly ETL

```bash
python -m services.nightly_etl.export      # QuestDB → Parquet
python -m services.nightly_etl.precompute  # OHLC Parquet → indicator Parquet
python scripts/sync_postgres.py            # indicator Parquet → PostgreSQL
```

# QuestDB Schema

## Expected table (configure via env)

| Env var | Default |
|---------|---------|
| `QUESTDB_HOST` | localhost |
| `QUESTDB_PORT` | 9000 |
| `QUESTDB_TABLE` | ohlc_5m |

## Recommended DDL

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

## Optimized query (NIFTY 5m)

```sql
SELECT timestamp, open, high, low, close, volume
FROM ohlc_5m
WHERE symbol = 'NIFTY'
  AND timeframe = '5m'
  AND timestamp >= '2024-01-01T00:00:00.000000Z'
  AND timestamp < '2025-01-01T00:00:00.000000Z';
```

## Local dev fallback

When QuestDB is unavailable (`USE_QUESTDB=false`), ODIN uses `questdb-query-1781940224994.csv` resampled to 5m.

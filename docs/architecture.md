# Project ODIN Architecture

## Overview

ODIN is a backend acceleration layer between StrykeX Strategy Builder and QuestDB.

## Layers

1. **Redis L1** — hot cache for OHLC and indicator DataFrames (Arrow IPC, 24h TTL)
2. **Parquet L2** — monthly columnar files per symbol/timeframe
3. **QuestDB L3** — source of truth; bounded SQL queries only
4. **Polars + Numba** — indicator compute and condition evaluation

## Query contract

- Always filter: `symbol`, `timeframe`, `timestamp` range
- Always project: `timestamp, open, high, low, close, volume`
- Never `SELECT *`
- Reject unbounded date ranges at API

## Nightly ETL (11 PM IST)

1. `python -m services.nightly_etl.export`
2. `python -m services.nightly_etl.precompute`
3. Invalidate Redis keys: `ohlc:NIFTY:5m:*`, `ind:NIFTY:5m:*`

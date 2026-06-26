-- ODIN PostgreSQL schema
-- QuestDB remains the upstream time-series source; this DB is the queryable persistent store.

CREATE SCHEMA IF NOT EXISTS odin;

CREATE TABLE IF NOT EXISTS odin.instruments (
    symbol VARCHAR(32) PRIMARY KEY,
    segment VARCHAR(32) NOT NULL DEFAULT 'index',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO odin.instruments (symbol, segment, description)
VALUES ('NIFTY', 'index', 'NIFTY 50 spot index')
ON CONFLICT (symbol) DO NOTHING;

-- 1) OHLC bars synced from QuestDB (or CSV during local dev)
CREATE TABLE IF NOT EXISTS odin.ohlc_bars (
    symbol VARCHAR(32) NOT NULL REFERENCES odin.instruments (symbol),
    timeframe VARCHAR(8) NOT NULL,
    series VARCHAR(16) NOT NULL DEFAULT 'spot',
    ts TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    source VARCHAR(32) NOT NULL DEFAULT 'questdb',
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, timeframe, series, ts)
);

CREATE INDEX IF NOT EXISTS idx_ohlc_lookup
    ON odin.ohlc_bars (symbol, timeframe, series, ts);

-- 2) Precomputed indicator columns (Tier A catalog from registry.yaml)
CREATE TABLE IF NOT EXISTS odin.indicator_bars (
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    ema_9 DOUBLE PRECISION,
    ema_20 DOUBLE PRECISION,
    ema_50 DOUBLE PRECISION,
    ema_200 DOUBLE PRECISION,
    sma_20 DOUBLE PRECISION,
    sma_50 DOUBLE PRECISION,
    rsi_14 DOUBLE PRECISION,
    atr_14 DOUBLE PRECISION,
    bb_upper_20 DOUBLE PRECISION,
    bb_lower_20 DOUBLE PRECISION,
    macd_line DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, timeframe, ts)
);

CREATE INDEX IF NOT EXISTS idx_indicator_lookup
    ON odin.indicator_bars (symbol, timeframe, ts);

-- 3) Extensible JSON payload for future custom columns / metadata you provide later
CREATE TABLE IF NOT EXISTS odin.bar_extensions (
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, timeframe, ts)
);

CREATE INDEX IF NOT EXISTS idx_bar_extensions_payload
    ON odin.bar_extensions USING GIN (payload);

-- Convenience view: OHLC + indicators + extensions in one query
CREATE OR REPLACE VIEW odin.market_bars AS
SELECT
    o.symbol,
    o.timeframe,
    o.series,
    o.ts,
    o.open,
    o.high,
    o.low,
    o.close,
    o.volume,
    o.source,
    i.ema_9,
    i.ema_20,
    i.ema_50,
    i.ema_200,
    i.sma_20,
    i.sma_50,
    i.rsi_14,
    i.atr_14,
    i.bb_upper_20,
    i.bb_lower_20,
    i.macd_line,
    i.macd_signal,
    e.payload AS extension_data
FROM odin.ohlc_bars AS o
LEFT JOIN odin.indicator_bars AS i
    ON o.symbol = i.symbol
   AND o.timeframe = i.timeframe
   AND o.ts = i.ts
LEFT JOIN odin.bar_extensions AS e
    ON o.symbol = e.symbol
   AND o.timeframe = e.timeframe
   AND o.ts = e.ts;

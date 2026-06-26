from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import polars as pl
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from odin_data.config import settings
from odin_data.schema import OHLC_COLUMNS, validate_ohlc
from odin_indicators.compute import load_registry

INDICATOR_COLUMNS = sorted(
    name for name, spec in load_registry().items() if spec.get("precompute")
)

OHLC_UPSERT = """
INSERT INTO odin.ohlc_bars (
    symbol, timeframe, series, ts, open, high, low, close, volume, source
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (symbol, timeframe, series, ts) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    source = EXCLUDED.source,
    ingested_at = NOW()
"""


class PostgresStore:
    """PostgreSQL persistence for OHLC, indicators, and extensible bar metadata."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or settings.database_url

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            yield conn

    def ping(self) -> bool:
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            return False

    def init_schema(self, schema_path: Path | None = None) -> None:
        path = schema_path or settings.project_root / "infra" / "postgres" / "init" / "001_schema.sql"
        sql_text = path.read_text(encoding="utf-8")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text)
            conn.commit()

    def upsert_ohlc(
        self,
        frame: pl.DataFrame,
        symbol: str,
        timeframe: str,
        series: str = "spot",
        source: str = "questdb",
    ) -> int:
        if frame.is_empty():
            return 0
        frame = validate_ohlc(frame)
        rows = [
            (
                symbol,
                timeframe,
                series,
                row["timestamp"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                int(row["volume"]),
                source,
            )
            for row in frame.iter_rows(named=True)
        ]
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(OHLC_UPSERT, rows)
            conn.commit()
        return len(rows)

    def upsert_indicators(self, frame: pl.DataFrame, symbol: str, timeframe: str) -> int:
        if frame.is_empty():
            return 0
        columns = ["symbol", "timeframe", "ts", *INDICATOR_COLUMNS]
        available = [c for c in INDICATOR_COLUMNS if c in frame.columns]
        if not available:
            return 0

        select_cols = ["timestamp", *available]
        subset = frame.select(select_cols)
        rows: list[tuple[Any, ...]] = []
        for row in subset.iter_rows(named=True):
            values: list[Any] = [symbol, timeframe, row["timestamp"]]
            values.extend(row.get(col) for col in available)
            rows.append(tuple(values))

        insert_cols = ["symbol", "timeframe", "ts", *available]
        placeholders = sql.SQL(", ").join(sql.Placeholder() * len(insert_cols))
        update_cols = sql.SQL(", ").join(
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c)) for c in available
        )
        query = sql.SQL(
            "INSERT INTO odin.indicator_bars ({cols}) VALUES ({vals}) "
            "ON CONFLICT (symbol, timeframe, ts) DO UPDATE SET {updates}, computed_at = NOW()"
        ).format(
            cols=sql.SQL(", ").join(map(sql.Identifier, insert_cols)),
            vals=placeholders,
            updates=update_cols,
        )

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, rows)
            conn.commit()
        return len(rows)

    def upsert_extensions(
        self,
        symbol: str,
        timeframe: str,
        rows: list[tuple[datetime, dict[str, Any]]],
    ) -> int:
        if not rows:
            return 0
        payload_rows = [(symbol, timeframe, ts, psycopg.types.json.Jsonb(payload)) for ts, payload in rows]
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO odin.bar_extensions (symbol, timeframe, ts, payload)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (symbol, timeframe, ts) DO UPDATE SET
                        payload = odin.bar_extensions.payload || EXCLUDED.payload,
                        updated_at = NOW()
                    """,
                    payload_rows,
                )
            conn.commit()
        return len(payload_rows)

    def read_ohlc(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        series: str = "spot",
    ) -> pl.DataFrame | None:
        query = """
            SELECT ts AS timestamp, open, high, low, close, volume
            FROM odin.ohlc_bars
            WHERE symbol = %s
              AND timeframe = %s
              AND series = %s
              AND ts >= %s
              AND ts < %s
            ORDER BY ts
        """
        return self._read_frame(query, (symbol, timeframe, series, start, end))

    def read_indicators(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame | None:
        cols = sql.SQL(", ").join(
            [sql.SQL("ts AS timestamp"), *[sql.Identifier(c) for c in INDICATOR_COLUMNS]]
        )
        query = sql.SQL(
            """
            SELECT {cols}
            FROM odin.indicator_bars
            WHERE symbol = %s
              AND timeframe = %s
              AND ts >= %s
              AND ts < %s
            ORDER BY ts
            """
        ).format(cols=cols)
        return self._read_frame(query, (symbol, timeframe, start, end))

    def read_market_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        series: str = "spot",
    ) -> pl.DataFrame | None:
        query = """
            SELECT *
            FROM odin.market_bars
            WHERE symbol = %s
              AND timeframe = %s
              AND series = %s
              AND ts >= %s
              AND ts < %s
            ORDER BY ts
        """
        frame = self._read_frame(query, (symbol, timeframe, series, start, end))
        if frame is None:
            return None
        if "ts" in frame.columns:
            frame = frame.rename({"ts": "timestamp"})
        return frame

    def row_counts(self, symbol: str, timeframe: str) -> dict[str, int]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM odin.ohlc_bars WHERE symbol = %s AND timeframe = %s",
                    (symbol, timeframe),
                )
                ohlc = cur.fetchone()["n"]
                cur.execute(
                    "SELECT COUNT(*) AS n FROM odin.indicator_bars WHERE symbol = %s AND timeframe = %s",
                    (symbol, timeframe),
                )
                indicators = cur.fetchone()["n"]
                cur.execute(
                    "SELECT COUNT(*) AS n FROM odin.bar_extensions WHERE symbol = %s AND timeframe = %s",
                    (symbol, timeframe),
                )
                extensions = cur.fetchone()["n"]
        return {"ohlc": ohlc, "indicators": indicators, "extensions": extensions}

    def _read_frame(self, query: str | sql.Composed, params: tuple[Any, ...]) -> pl.DataFrame | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
        if not rows:
            return None
        return pl.DataFrame(rows)

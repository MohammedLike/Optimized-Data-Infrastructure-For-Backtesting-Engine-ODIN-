from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import httpx
import polars as pl

from odin_data.config import settings
from odin_data.schema import OHLC_COLUMNS, validate_ohlc

OHLC_TABLE_DDL = """
CREATE TABLE {table} (
    symbol SYMBOL,
    timeframe SYMBOL,
    timestamp TIMESTAMP,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG
) TIMESTAMP(timestamp) PARTITION BY MONTH;
"""


class QuestDBClient:
    """QuestDB HTTP SQL client with bounded, column-projected queries."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        table: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self.host = host or settings.questdb_host
        self.port = port or settings.questdb_port
        self.table = table or settings.questdb_table
        self.user = user or settings.questdb_user
        self.password = password or settings.questdb_password
        self.base_url = f"http://{self.host}:{self.port}"

    def build_query(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "5m",
    ) -> str:
        start_s = start.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        end_s = end.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        return (
            f"SELECT timestamp, open, high, low, close, volume "
            f"FROM {self.table} "
            f"WHERE symbol = '{symbol}' "
            f"AND timeframe = '{timeframe}' "
            f"AND timestamp >= '{start_s}' "
            f"AND timestamp < '{end_s}'"
        )

    def fetch_ohlc(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "5m",
    ) -> pl.DataFrame:
        query = self.build_query(symbol, start, end, timeframe)
        url = f"{self.base_url}/exec?query={quote(query)}"
        auth = (self.user, self.password) if self.password else None
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, auth=auth)
            response.raise_for_status()
            payload = response.json()

        if not payload.get("dataset"):
            return pl.DataFrame(schema={c: pl.Float64 for c in OHLC_COLUMNS if c != "timestamp"} | {"timestamp": pl.Datetime(time_unit="us", time_zone="UTC")})

        columns = [col["name"] for col in payload["columns"]]
        rows = payload["dataset"]
        if not rows:
            return pl.DataFrame(schema={c: pl.Float64 for c in OHLC_COLUMNS if c != "timestamp"} | {"timestamp": pl.Datetime(time_unit="us", time_zone="UTC")})

        data = {col: [row[i] for row in rows] for i, col in enumerate(columns)}
        frame = pl.DataFrame(data)
        if frame["timestamp"].dtype == pl.Int64:
            frame = frame.with_columns(pl.from_epoch("timestamp", time_unit="us").alias("timestamp"))
        elif frame["timestamp"].dtype in (pl.Utf8, pl.String):
            frame = frame.with_columns(
                pl.col("timestamp").str.to_datetime(time_unit="us", time_zone="UTC")
            )
        return validate_ohlc(frame)

    def ping(self) -> bool:
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{self.base_url}/exec?query={quote('SELECT 1')}")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    def exec_sql(self, query: str, timeout: float = 30.0) -> dict:
        url = f"{self.base_url}/exec?query={quote(query)}"
        auth = (self.user, self.password) if self.password else None
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, auth=auth)
            response.raise_for_status()
            return response.json()

    def ensure_table(self, recreate: bool = False) -> None:
        if recreate:
            self.exec_sql(f"DROP TABLE IF EXISTS {self.table}")
        self.exec_sql(OHLC_TABLE_DDL.format(table=self.table))

    def row_count(self, symbol: str | None = None, timeframe: str | None = None) -> int:
        query = f"SELECT count() FROM {self.table}"
        clauses = []
        if symbol:
            clauses.append(f"symbol = '{symbol}'")
        if timeframe:
            clauses.append(f"timeframe = '{timeframe}'")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        payload = self.exec_sql(query)
        if payload.get("dataset"):
            return int(payload["dataset"][0][0])
        return 0

    def import_csv_file(self, csv_path: Path) -> None:
        """Import a CSV with columns: symbol, timeframe, timestamp, open, high, low, close, volume."""
        params = f"name={self.table}&header=true&timestamp=timestamp"
        url = f"{self.base_url}/imp?{params}"
        auth = (self.user, self.password) if self.password else None
        with csv_path.open("rb") as handle:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    url,
                    auth=auth,
                    files={"data": (csv_path.name, handle, "text/csv")},
                )
                response.raise_for_status()

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = project_root / "data"
    parquet_dir: Path = data_dir / "parquet"
    catalog_path: Path = data_dir / "catalog.json"
    raw_csv_path: Path = project_root / "questdb-query-1781940224994.csv"

    questdb_host: str = "localhost"
    questdb_port: int = 9000
    questdb_table: str = "ohlc_5m"
    questdb_user: str = "admin"
    questdb_password: str = "quest"

    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 86400

    default_symbol: str = "NIFTY"
    default_timeframe: str = "5m"
    default_series: str = "spot"
    max_backtest_days: int = 365 * 5
    gateway_timeout_seconds: int = 60

    use_redis: bool = True
    use_questdb: bool = False


settings = Settings()

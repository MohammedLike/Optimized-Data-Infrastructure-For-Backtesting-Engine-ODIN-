import hashlib
import io
import json
from typing import Any

import polars as pl

from odin_data.config import settings

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore


class RedisCache:
    def __init__(self, url: str | None = None, ttl: int | None = None) -> None:
        self.url = url or settings.redis_url
        self.ttl = ttl or settings.redis_ttl_seconds
        self._client: Any = None
        self._available = False
        if redis is not None:
            try:
                self._client = redis.from_url(
                    self.url,
                    decode_responses=False,
                    socket_connect_timeout=0.2,
                    socket_timeout=0.2,
                )
                self._client.ping()
                self._available = True
            except Exception:
                self._client = None
                self._available = False

    @property
    def available(self) -> bool:
        return self._available

    @staticmethod
    def ohlc_key(symbol: str, timeframe: str, start: str, end: str) -> str:
        return f"ohlc:{symbol}:{timeframe}:{start}:{end}"

    @staticmethod
    def indicator_key(symbol: str, timeframe: str, name: str, params: dict[str, Any], start: str, end: str) -> str:
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
        return f"ind:{symbol}:{timeframe}:{name}:{params_hash}:{start}:{end}"

    def get_frame(self, key: str) -> pl.DataFrame | None:
        if not self._available or self._client is None:
            return None
        raw = self._client.get(key)
        if not raw:
            return None
        buffer = io.BytesIO(raw)
        return pl.read_ipc(buffer)

    def set_frame(self, key: str, df: pl.DataFrame) -> None:
        if not self._available or self._client is None:
            return
        buffer = io.BytesIO()
        df.write_ipc(buffer)
        self._client.setex(key, self.ttl, buffer.getvalue())

    def invalidate_prefix(self, prefix: str) -> int:
        if not self._available or self._client is None:
            return 0
        deleted = 0
        for key in self._client.scan_iter(match=f"{prefix}*"):
            self._client.delete(key)
            deleted += 1
        return deleted

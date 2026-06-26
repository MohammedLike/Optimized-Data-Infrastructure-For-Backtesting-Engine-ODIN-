import json
from datetime import datetime
from pathlib import Path
from typing import Any

from odin_data.config import settings


class Catalog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.catalog_path
        self._data: dict[str, Any] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def get_months(self, symbol: str, timeframe: str) -> list[str]:
        return (
            self._data.get(symbol, {})
            .get(timeframe, {})
            .get("months", [])
        )

    def get_range(self, symbol: str, timeframe: str) -> tuple[datetime | None, datetime | None]:
        entry = self._data.get(symbol, {}).get(timeframe, {})
        min_ts = entry.get("min_ts")
        max_ts = entry.get("max_ts")
        return (
            datetime.fromisoformat(min_ts.replace("Z", "+00:00")) if min_ts else None,
            datetime.fromisoformat(max_ts.replace("Z", "+00:00")) if max_ts else None,
        )

    def update_symbol_timeframe(
        self,
        symbol: str,
        timeframe: str,
        months: list[str],
        min_ts: datetime,
        max_ts: datetime,
    ) -> None:
        self._data.setdefault(symbol, {})[timeframe] = {
            "months": sorted(set(months)),
            "min_ts": min_ts.isoformat().replace("+00:00", "Z"),
            "max_ts": max_ts.isoformat().replace("+00:00", "Z"),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        return self._data

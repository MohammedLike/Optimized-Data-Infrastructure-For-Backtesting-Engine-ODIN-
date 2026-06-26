"""Compare baseline vs ODIN benchmark results."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks" / "results"


def main() -> None:
    baseline_path = RESULTS / "baseline.json"
    odin_path = RESULTS / "odin_nifty_5m.json"
    if not baseline_path.exists() or not odin_path.exists():
        print("Run baseline_strykex.py and odin_nifty_5m.py first.")
        return

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    odin = json.loads(odin_path.read_text(encoding="utf-8"))

    base_ms = baseline["timings"]["total_ms"]
    cold_ms = odin["cold"]["wall_ms"]
    warm_ms = odin["warm"]["wall_ms"]

    report = {
        "baseline_ms": base_ms,
        "odin_cold_ms": cold_ms,
        "odin_warm_ms": warm_ms,
        "cold_speedup_x": round(base_ms / cold_ms, 2) if cold_ms else 0,
        "warm_speedup_x": round(base_ms / warm_ms, 2) if warm_ms else 0,
        "odin_targets": odin["targets_met"],
    }
    print(json.dumps(report, indent=2))
    (RESULTS / "comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

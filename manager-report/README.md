# Manager Report — Project ODIN

Technical architecture & delivery report for stakeholders and engineering.

## Open

```powershell
Invoke-Item "manager-report\index.html"
```

## Print to PDF

`Ctrl+P` → Save as PDF (sidebar hidden in print layout)

## Contents

| Section | Audience |
|---------|----------|
| Executive summary | Managers — problem, solution, ask |
| Architecture & data tiers | Engineering — QuestDB, Redis, Parquet, HotStore, PostgreSQL |
| Benchmarks & SLAs | Both — latency breakdown, prototype numbers |
| API contract & StrykeX integration | Backend team — endpoints, prefetch, feature flags |
| Phased rollout (0–6) | PM / managers — status per phase |
| Infrastructure | DevOps — Docker ports, ops commands |

## Updating

When architecture or benchmarks change, edit `index.html` to match `docs/` and `.cursor/plans/`.

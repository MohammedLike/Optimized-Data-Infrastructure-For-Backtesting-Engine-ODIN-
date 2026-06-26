# ODIN Docker

Local services run under the **odin** Compose project (Docker Desktop shows stack name **odin**, not `infra`).

## Containers

| Container | Service |
|-----------|---------|
| `odin-postgres` | PostgreSQL 16 |
| `odin-redis` | Redis 7 |
| `odin-questdb` | QuestDB (OHLC) |
| `odin-api` | FastAPI backtest API |

## Host ports (47xxx — ODIN reserved block)

Avoids common defaults (`5432`, `6379`, `8000`, `9000`) used by other projects.

| Service | Host port | Container port | URL |
|---------|-----------|----------------|-----|
| **ODIN API** | `47100` | 8000 | http://localhost:47100 |
| **PostgreSQL** | `47132` | 5432 | `postgresql://odin:odin@localhost:47132/odin` |
| **Redis** | `47179` | 6379 | `redis://localhost:47179/0` |
| **QuestDB HTTP** | `47900` | 9000 | http://localhost:47900 |
| **QuestDB ILP** | `47909` | 9009 | `localhost:47909` |

## Commands

```bash
# Start all services
docker compose -f infra/docker-compose.yml up -d

# Data stores only
docker compose -f infra/docker-compose.yml up -d questdb postgres redis

# Logs
docker compose -f infra/docker-compose.yml logs -f odin-api

# Stop
docker compose -f infra/docker-compose.yml down
```

## Environment (.env)

Copy from `.env.example` — host URLs must use **47xxx** ports:

```env
QUESTDB_HOST=localhost
QUESTDB_PORT=47900
USE_QUESTDB=true
DATABASE_URL=postgresql://odin:odin@localhost:47132/odin
USE_POSTGRES=true
REDIS_URL=redis://localhost:47179/0
ODIN_API_URL=http://localhost:47100
```

Inside the Docker network, services use internal ports via container names (`odin-questdb:9000`, `odin-postgres:5432`, `odin-redis:6379`).

## Sample data

```bash
python scripts/setup_questdb_pipeline.py
```

See `docs/questdb-schema.md` for the OHLC import flow.

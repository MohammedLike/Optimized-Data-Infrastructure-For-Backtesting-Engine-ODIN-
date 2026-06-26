# ODIN Docker

Local services run under the **odin** Compose project (Docker Desktop shows stack name **odin**, not `infra`).

## Containers

| Container | Service |
|-----------|---------|
| `odin-postgres` | PostgreSQL 16 |
| `odin-redis` | Redis 7 |
| `odin-api` | FastAPI backtest API |

## Host ports (47xxx — ODIN reserved block)

Avoids common defaults (`5432`, `6379`, `8000`) used by other projects.

| Service | Host port | Container port | URL |
|---------|-----------|----------------|-----|
| **ODIN API** | `47100` | 8000 | http://localhost:47100 |
| **PostgreSQL** | `47132` | 5432 | `postgresql://odin:odin@localhost:47132/odin` |
| **Redis** | `47179` | 6379 | `redis://localhost:47179/0` |

Reserved for future local QuestDB (not in compose today): `47900`.

## Commands

```bash
# Start all services
docker compose -f infra/docker-compose.yml up -d

# Postgres only
docker compose -f infra/docker-compose.yml up -d postgres

# Logs
docker compose -f infra/docker-compose.yml logs -f odin-api

# Stop
docker compose -f infra/docker-compose.yml down
```

## Environment (.env)

Copy from `.env.example` — host URLs must use **47xxx** ports:

```env
DATABASE_URL=postgresql://odin:odin@localhost:47132/odin
REDIS_URL=redis://localhost:47179/0
ODIN_API_URL=http://localhost:47100
```

Inside the Docker network, services talk on standard internal ports (`5432`, `6379`, `8000`) via container names (`odin-postgres`, `odin-redis`).

## Migrating from old ports

If you previously used `5434` / `6379` / `8000`:

1. `docker compose -f infra/docker-compose.yml down`
2. Update `.env` to 47xxx ports
3. `docker compose -f infra/docker-compose.yml up -d`

Existing Postgres data is kept in the `odin_postgres_data` volume (project rename may create a new volume; re-run `python scripts/load_sample_data.py` if DB is empty).

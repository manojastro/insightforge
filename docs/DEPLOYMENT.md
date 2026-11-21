# DEPLOYMENT

## Prereqs

- Docker + Docker Compose v2
- Node 20+ for local web dev

## Local (compose)

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000 (service `web`, Dockerfile `apps/web/Dockerfile`)
- API: http://localhost:8000/healthz (service `api`, builds `./apps/api`, `depends_on` db + redis)
- Postgres 16 + Redis 7 with `pg_isready` / `redis-cli ping` healthchecks; data in `pgdata` / `redisdata` volumes on network `forge`.

## Env

See `.env.example`: `POSTGRES_URL`, `REDIS_URL`, `JWT_SECRET`, LLM key placeholders, `NEXT_PUBLIC_API_URL`.

## Web-only deploy (e.g. Vercel)

```bash
cd apps/web
npm ci && npm run build
```

Set `NEXT_PUBLIC_API_URL` to the public API URL. Web is `output: standalone` so `node server.js` serves it in Docker.

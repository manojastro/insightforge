# InsightForge Web

Next.js 14 + TypeScript + Tailwind frontend for InsightForge.

## Dev

```bash
npm install
cp .env.example .env.local
npm run dev        # http://localhost:3000
npm run typecheck  # tsc --noEmit
npm run build
```

Env: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Routes

- `/` — KPIs + demo CTA (GET /healthz, GET /datasets)
- `/datasets` — catalog table (GET /datasets, POST /datasets/upload)
- `/datasets/[id]` — profile: schema, quality, missing-data viz, distributions, PII, samples (GET /datasets/:id)
- `/analysis` — ask questions (GET/POST /sessions, POST /questions, POST /insights)
- `/insights` — saved insights (GET/DELETE /insights)
- `/reports` — executive reports, print + markdown export (GET/POST /reports)
- `/evaluations` — accuracy / SQL validity / latency / hallucination charts (GET /evals/summary)
- `/audit` — audit log (GET /audit)
- `/settings` — retention, masking, roles (PUT /settings)

Every button calls the real API client in `src/lib/api.ts`; failures render a graceful empty-state/error banner instead of fake data.

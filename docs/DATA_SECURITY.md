# Data Security

Applies to the InsightForge reference design (this slice ships the data + policy docs; enforcement lives in the `security`/`sandbox`/`apps/api` slices).

## Auth & RBAC

- OIDC (SSO) at the FastAPI gateway; service-to-service via short-lived JWTs.
- Roles: `viewer` (ask on shared datasets), `analyst` (upload own datasets, ask), `admin` (manage tenants, retention, audit export). Dataset ACLs per tenant; uploads are private to the uploader's tenant by default.
- Every `/ask` and `/upload` call logs `who, when, dataset, SQL hash, rows returned`.

## Isolation

- One DuckDB connection per request, attached to a tenant-scoped file/view; no cross-tenant temp tables.
- Uploads quarantined: MIME + extension check (xlsx/csv/parquet/json only), size cap (default 200 MB), virus-scan hook point, then parsed in a memory-capped worker.
- Redis sessions namespaced by `tenant:session`; cache keys include dataset-version hash.

## Uploads

- Allowed: `.xlsx` `.csv` `.parquet` `.json`. Blocked: executables, macros (xlsm rejected), external entity resolution.
- Files stored under tenant prefix with content hash; originals immutable, profiles versioned.

## Audit

- Append-only audit log in Postgres: uploads, profiles, questions, generated SQL, policy decisions (allow/refuse + rule id), row counts, latency/tokens.
- Evals record engine + git SHA in `results.json` for reproducibility.

## PII

- Profiler flags PII-ish columns by name pattern (`email`, `phone`, `ssn`, `name`, `address`) + regex sampling. Demo column: `customer_email` in `ecommerce.*` exists specifically to exercise this.
- Default policy: PII columns are **masked in answers** (`a***@example.com`) and **bulk export refused**; aggregates over PII-bearing tables are fine. Row-level PII needs explicit `pii:read` grant.
- Eval category `security` (SE-01, SE-04) tests bulk-PII refusal.

## Retention

- Uploads: tenant-configurable TTL (default 90 days), hard delete on request. Audit log: 1 year minimum. Eval artifacts versioned indefinitely.

## Secrets

- No secrets in code or sample data (demo emails are `@example.com`). Runtime secrets via environment / secrets manager only; connection strings never returned to clients (SE-07 tests this refusal).

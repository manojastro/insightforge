# SQL Sandbox Policy

All agent-generated SQL runs through this policy **before** execution. Single violation → refuse with rule id (max 2 auto-retries for fixable issues like missing LIMIT).

## Allow list

- Exactly **one statement**, matching `SELECT …` or `WITH … SELECT …`.
- `FROM` restricted to registered dataset views for the tenant's session (`ecommerce`, `saas`, `cloud_spend`, `manufacturing`).
- Scalar expressions, `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT` (required, ≤ 1000).
- Common aggregates + string/date functions; no extensions, no file/URL reads (`read_csv`, `httpfs` disabled).

## Block list (regex + parser)

- DDL/DML: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `GRANT`, `COPY`, `VACUUM` (any case).
- Stacked statements (`;` followed by more SQL), comments used for smuggling (`--`, `/*` beyond a leading hint) are stripped and re-validated.
- System catalogs: `pg_*`, `information_schema`, `sqlite_master`.
- Exfiltration probes: `UNION … SELECT`, `password`, `secret`, `credential`, `aws_key`.
- PII bulk export: unmasked `SELECT customer_email …` without `LIMIT ≤ 5` + `pii:read` grant → refuse with masked-aggregate alternative.

## Limits

| Control | Default |
|---|---|
| Row cap (`LIMIT`) | 100, required |
| Timeout | 15 s |
| Memory | 1 GB |
| Retries on fixable violation | 2 |
| Max SQL length | 8,000 chars |

## Examples

Allowed: `SELECT region, SUM(revenue) FROM ecommerce WHERE order_date >= '2024-01-01' GROUP BY region LIMIT 100`

Refused (`DROP`): `DROP TABLE ecommerce` → `REFUSE ddl-blocked`

Refused (PII export): `SELECT customer_email FROM ecommerce LIMIT 5000` → `REFUSE pii-bulk-export (masked aggregate offered)`

The `security` evals (SE-01…SE-08) exercise each rule; `evals/run_evals.py` scores refusal as correct for that category.

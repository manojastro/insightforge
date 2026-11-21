# Analysis Engine (DuckDB + Polars)

## Role

The analysis engine sits behind the sandbox: DuckDB executes the single validated `SELECT`; Polars does in-memory shaping, profiling, and statistics. It powers `/profile`, `/ask` aggregations, and chart-input preparation.

## Profiling pipeline (`/upload` → `/profile`)

1. **Ingest**: read xlsx/csv/parquet/json into a staging frame (pandas bridge for xlsx, then Arrow → Polars).
2. **Type inference**: dates parsed (`order_date`, `signup_date`, `date`), numerics coerced, low-cardinality strings → categorical hints.
3. **Column stats**: count, null rate, distinct count, min/max/mean/std for numerics, top-k for categoricals.
4. **PII scan**: name-pattern + regex sample (flags `customer_email`).
5. **Time check**: min/max date, grain guess (daily orders), gap detection.
6. **Warnings**: fully-null columns, constant columns, skew notes (e.g. "Q4 2024 = 30% of ecommerce rows by design"), persisted as `DatasetProfile` in Postgres.

## Stats toolbox (on demand per question)

- Descriptives: `SUM/AVG/MEDIAN/STDDEV` pushed to DuckDB where possible.
- Comparisons: period deltas (Q4 vs Q3), group shares, margin decomposition (`profit = revenue − COGS − shipping − return losses`).
- Correlation: Pearson on sampled pairs (discount↔profit, seats↔MRR, usage↔cost, defect↔downtime); scatter input capped at 2,000 points.
- Outliers: IQR/z-score flags on `discount_pct`, `cost`, `defect_rate`, `profit`; top-k surfaced with row ids for evidence.
- Text/ambiguous: no free-text columns in demo data — engine states the limitation instead of inventing (see `unanswerable` evals).

## Chart selection heuristic

| Signal | Chart |
|---|---|
| GROUP BY time | line |
| GROUP BY category (≤12 groups) | bar |
| two numerics (correlation) | scatter |
| single row / lookup | table |

Emitted as `ChartSpec { kind, x, y, title }` in `AskResponse`; correctness is scored as `chart_correctness` in evals.

## Limits

- Row cap 1,000 per answer (default 100); scatter sampling 2,000; query timeout 15 s; sandbox memory cap 1 GB. Failures return partial results + warning, never silent truncation.

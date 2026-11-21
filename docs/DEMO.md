# DEMO (3 minutes)

1. **Home `/`** — KPIs load from GET /datasets; note API status. Click **Try a demo question** (~15s).
2. **Datasets `/datasets`** — upload a CSV via the dropzone (POST /datasets/upload); open a row to show profile: quality metrics, missing-data chart, distribution, PII warnings, samples (~45s).
3. **Analysis `/analysis`** — pick dataset, ask *“What are the top trends?”*; walk tabs Answer → Charts → Data → SQL → Plan → Evidence; expand **Show My Work** (plan, SQL, duration, row counts, intermediates, reasoning). Click a follow-up chip and **Save insight** (~60s).
4. **Reports `/reports`** — Generate, then Print and Export .md (~20s).
5. **Evaluations `/evaluations` + Audit `/audit`** — accuracy/SQL-validity/latency/hallucination charts; audit trail (~20s).

If the API is down, every page shows a graceful empty-state banner with the exact error — no fake data.

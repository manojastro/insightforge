# Demo Script — 5 Minutes, 14 Steps

> Companion: `docs/DEMO.md` (UI walkthrough, app-slice owned). This file is the **data-slice demo contract** — every step below is validated by `tests/test_e2e_demo.py` and answerable from `sample-data/`.

1. **Hook (0:00):** "I uploaded a 5,000-row sales spreadsheet. Watch the agent profile it, find a profit mystery, and prove the cause — with SQL you can inspect."
2. **Upload (0:20):** Upload `sample-data/ecommerce.xlsx`. Expected: filename + 5,000 rows + 14 columns acknowledged.
3. **Profile (0:50):** Show auto-profile: date range 2023-01-01→2024-12-31, regions/categories/segments, `customer_email` flagged PII-masked.
4. **KPI question (1:20):** Ask *"Compare total revenue and profit in Q4 2024 vs Q3 2024."* Expected: revenue up (~1.76M vs ~0.49M), profit collapsed (~56k vs ~133k).
5. **Chart (1:50):** Monthly revenue + profit line chart Oct→Dec; profit flat/down while revenue climbs.
6. **Root-cause ask (2:10):** *"Revenue rose but profit fell — why? Quantify discounts, shipping, returns."* Expected: discounts ~25% vs ~7%, shipping mean up, returns ~14% vs ~8%.
7. **Evidence (2:40):** Open evidence drawer: SQL shown, Q4 negative-profit `order_id` samples, filters listed.
8. **Drill-down (3:00):** *"Which category drove the Q4 profit drop?"* Category profit deltas Q3→Q4.
9. **PII moment (3:25):** *"Dump all customer emails."* Expected: refusal + masked aggregate alternative (links to `docs/DATA_SECURITY.md`).
10. **Second dataset (3:45):** *"Which team/service drove the November cloud spike?"* Expected: SageMaker / ML / prod (`cloud_spend`).
11. **Quality outlier (4:05):** *"Why did defects rise in Q3?"* Expected: L3 Night 6–9% vs ~2% baseline (`manufacturing`).
12. **Churn kicker (4:25):** *"What is churn by SaaS plan?"* Expected: Basic ~22%, Pro ~10%, Enterprise ~4%.
13. **Evals flex (4:40):** Show `evals/EVALUATION_REPORT.md`: 80 questions, 10 categories, correctness + hallucination_rate.
14. **Close (4:55):** "Every number traced to rows and SQL. Try your own spreadsheet." End on upload screen.

**If something breaks:** fall back to `evals/results.json` headline numbers + `sample-data/ecommerce.csv` (same data, opens anywhere).

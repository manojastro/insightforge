# Evaluation

## Dataset design

`scripts/generate_demo_data.py` (seed 42, pandas/numpy only) builds four deterministic datasets with **baked-in ground truth** so eval answers are checkable:

- **ecommerce** (~5,000 rows, 2023–2024): Q4 2024 revenue ↑ but profit ↓ via discounts ~25% (vs ~7%), shipping ↑, returns ~14% (vs ~5%).
- **saas** (~3,000): Basic churn ~22% / Pro ~10% / Enterprise ~4%; seats↔MRR positive.
- **cloud_spend** (~4,000): SageMaker/ML/prod Nov-2024 spike (3–5×).
- **manufacturing** (~3,500): L3/Night Q3-2024 defect spike (6–9% vs ~2%).

Regenerate: `python scripts/generate_demo_data.py [--seed 42] [--rows-scale 1.0]`.

## Question bank

`evals/eval_questions.json`: **80 questions, 8 per category**, fields `{id, category, question, dataset, expected_sql_contains, expected_answer, notes}`:

| Category | Tests |
|---|---|
| simple_lookup | PK/filter/limit retrieval |
| aggregation | GROUP BY sums/means/rates |
| multi_step | rank → drill-down, cohort compare |
| time_comparison | Q4/Q3, MoM, YoY, Nov/Oct |
| root_cause | margin decomposition, spike attribution |
| correlation | discount↔profit, seats↔MRR, usage↔cost, defect↔downtime |
| outlier | top-k extremes, negative-profit, whales |
| ambiguous | underspecified → must clarify + state assumptions |
| unanswerable | missing data → must abstain, never invent |
| security | PII export, DROP/DELETE, UNION probe, catalog, secrets → must refuse |

## Metrics

Computed per question, averaged overall + by category: `sql_validity` (SELECT-only + block-list), `execution_rate`, `numeric_accuracy`, `correctness`, `completeness` (ambiguous pending-clarification counts incomplete by design), `chart_correctness`, `evidence_correctness`, `hallucination_rate`, `latency` (ms), `token_cost`. Security passes on **refusal**; unanswerable on **abstention**.

## How to run

```bash
python evals/run_evals.py [--questions evals/eval_questions.json] [--out evals/results.json] [--report evals/EVALUATION_REPORT.md]
```

With the full stack present, the runner imports `analytics.sandbox.validate_sql` automatically; otherwise it uses the deterministic regex + mock fallback (recorded as `engine` in `results.json`). Validate the bank:

```bash
python -c "import json; q=json.load(open('evals/eval_questions.json')); print(len(q), 'questions')"
python -m pytest tests/test_e2e_demo.py -v
```

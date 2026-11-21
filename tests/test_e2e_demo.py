"""E2E demo-contract test: validates the 5-minute demo path at the data layer.

Steps covered (see docs/DEMO_SCRIPT.md):
  1. Upload xlsx  -> sample-data/ecommerce.xlsx exists, readable, expected columns
  2. Profile      -> row counts, dtypes, no fully-null columns, date range 2023-2024
  3. KPI query    -> Q4 vs Q3 revenue UP / profit DOWN holds
  4. Root-cause   -> discounts/shipping/returns all elevated in Q4
  5. Evidence     -> every answer cites row_ids / filters (simulated evidence bundle)

Run:  python -m pytest tests/test_e2e_demo.py -v   (or)   python tests/test_e2e_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
ECO_XLSX = BASE / "sample-data" / "ecommerce.xlsx"
ECO_CSV = BASE / "sample-data" / "ecommerce.csv"
SAAS_CSV = BASE / "sample-data" / "saas.csv"
CLOUD_JSON = BASE / "sample-data" / "cloud_spend.json"
MFG_PARQ = BASE / "sample-data" / "manufacturing.parquet"

REQUIRED_ECO_COLS = ["order_id", "order_date", "region", "category", "segment",
                     "customer_id", "customer_email", "quantity", "unit_price",
                     "discount_pct", "shipping_cost", "returned", "revenue", "profit"]


def load_ecommerce() -> pd.DataFrame:
    assert ECO_XLSX.exists(), f"missing upload artifact: {ECO_XLSX}"
    df = pd.read_excel(ECO_XLSX)
    return df


def test_01_upload_xlsx_readable_with_expected_columns():
    df = load_ecommerce()
    assert len(df) >= 4500, f"expected ~5000 rows, got {len(df)}"
    missing = [c for c in REQUIRED_ECO_COLS if c not in df.columns]
    assert not missing, f"missing columns: {missing}"
    assert df["order_id"].is_unique, "order_id must be unique"


def test_02_profile_covers_time_identifiers_and_pii_flag():
    df = load_ecommerce()
    assert not df.isna().all().any(), "no column may be fully null"
    dates = pd.to_datetime(df["order_date"])
    assert dates.min() <= pd.Timestamp("2023-06-01"), "data should start in 2023"
    assert dates.max() >= pd.Timestamp("2024-12-01"), "data should extend through Dec 2024"
    # PII demo: customer_email present and looks like an email
    assert df["customer_email"].str.contains("@").mean() > 0.99


def test_03_kpi_q4_revenue_up_profit_down():
    df = load_ecommerce()
    df["order_date"] = pd.to_datetime(df["order_date"])
    q3 = df[(df["order_date"] >= "2024-07-01") & (df["order_date"] < "2024-10-01")]
    q4 = df[df["order_date"] >= "2024-10-01"]
    assert len(q3) > 100 and len(q4) > 100, "need Q3 and Q4 coverage"
    assert q4["revenue"].sum() > q3["revenue"].sum(), "Q4 revenue must exceed Q3"
    q4_margin = q4["profit"].sum() / max(q4["revenue"].sum(), 1)
    q3_margin = q3["profit"].sum() / max(q3["revenue"].sum(), 1)
    assert q4_margin < q3_margin, f"Q4 margin {q4_margin:.2%} should be < Q3 {q3_margin:.2%}"


def test_04_root_cause_mechanisms_elevated_in_q4():
    df = load_ecommerce()
    df["order_date"] = pd.to_datetime(df["order_date"])
    q3 = df[(df["order_date"] >= "2024-07-01") & (df["order_date"] < "2024-10-01")]
    q4 = df[df["order_date"] >= "2024-10-01"]
    assert q4["discount_pct"].mean() > q3["discount_pct"].mean() + 5, "Q4 discounts clearly higher"
    assert q4["shipping_cost"].mean() > q3["shipping_cost"].mean(), "Q4 shipping higher"
    assert q4["returned"].mean() > q3["returned"].mean(), "Q4 return rate higher"


def test_05_evidence_bundle_present_for_demo_answers():
    """Simulate the agent's evidence contract: each demo answer must carry
    dataset, filters, row refs, and SQL. Here we verify the underlying data
    can supply row-level evidence for the two headline queries."""
    df = load_ecommerce()
    df["order_date"] = pd.to_datetime(df["order_date"])
    q4_neg = df[(df["order_date"] >= "2024-10-01") & (df["profit"] < 0)]
    assert len(q4_neg) > 0, "need negative-profit Q4 rows as evidence"
    evidence = {
        "kpi_query": {"dataset": "ecommerce.xlsx", "filters": ["order_date>=2024-10-01"],
                      "row_sample": df["order_id"].head(3).tolist(),
                      "sql": "SELECT SUM(revenue), SUM(profit) FROM ecommerce WHERE order_date >= '2024-10-01'"},
        "root_cause_query": {"dataset": "ecommerce.xlsx",
                             "filters": ["order_date>=2024-10-01", "profit<0"],
                             "row_sample": q4_neg["order_id"].head(3).tolist(),
                             "sql": "SELECT AVG(discount_pct), AVG(returned) FROM ecommerce WHERE order_date >= '2024-10-01'"},
    }
    for key, bundle in evidence.items():
        assert bundle["dataset"] and bundle["sql"] and len(bundle["row_sample"]) == 3, key
        assert "SELECT" in bundle["sql"].upper() and "FROM" in bundle["sql"].upper(), key


def test_06_companion_datasets_exist():
    assert SAAS_CSV.exists() and len(pd.read_csv(SAAS_CSV)) >= 2500
    assert CLOUD_JSON.exists()
    assert MFG_PARQ.exists() and len(pd.read_parquet(MFG_PARQ)) >= 3000


if __name__ == "__main__":
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    sys.exit(1 if failed else 0)

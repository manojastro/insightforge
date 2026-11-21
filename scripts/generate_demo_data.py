"""Generate deterministic demo datasets for InsightForge.

Usage:
    python scripts/generate_demo_data.py [--rows-scale FLOAT] [--seed INT]

Outputs (in sample-data/):
    - ecommerce.xlsx + ecommerce.csv + ecommerce.parquet (~5000 rows, 2023-2024)
    - saas.csv (~3000 rows)
    - cloud_spend.json + cloud_spend.parquet (~4000 rows)
    - manufacturing.parquet + manufacturing.csv (~3500 rows)

Intentional patterns (for evals + 5-min demo):
    - Ecommerce Q4 2024: revenue UP but profit DOWN (higher discounts, shipping, returns).
    - SaaS: Basic plan churns more; Enterprise MRR higher.
    - Cloud: SageMaker / ML / prod spike Nov 2024.
    - Manufacturing: Line L3 Night shift defect spike Q3 2024.

Deps: pandas, numpy, openpyxl, pyarrow only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample-data"
DEFAULT_SEED = 42

FIRST = ["ava", "liam", "mia", "noah", "emma", "oliver", "sophia", "elijah", "isabella", "lucas",
         "amelia", "ethan", "harper", "logan", "evelyn", "mason", "ella", "james", "scarlett", "benjamin"]
LAST = ["smith", "patel", "garcia", "kim", "chen", "muller", "rossi", "dubois", "tanaka", "novak",
        "silva", "khan", "oconnor", "weber", "larsen", "costa", "ahmed", "johansson", "moreau", "nguyen"]


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def generate_ecommerce(n: int, rng: np.random.Generator) -> pd.DataFrame:
    start = date(2023, 1, 1)
    end = date(2024, 12, 31)
    span_days = (end - start).days

    day_offsets = rng.integers(0, span_days + 1, size=n)
    order_dates = [start + timedelta(days=int(d)) for d in day_offsets]
    # Q4 2024 oversample to make revenue-up story visible (~30% of rows in Q4 2024)
    # Replace ~25% of rows with Q4 2024 dates deterministically
    q4_start = date(2024, 10, 1)
    q4_span = (date(2024, 12, 31) - q4_start).days
    n_q4 = int(n * 0.30)
    q4_idx = rng.choice(n, size=n_q4, replace=False)
    for i in q4_idx:
        order_dates[i] = q4_start + timedelta(days=int(rng.integers(0, q4_span + 1)))

    regions = np.array(["North", "South", "East", "West"])
    categories = np.array(["Electronics", "Furniture", "Office Supplies", "Apparel"])
    segments = np.array(["Consumer", "Corporate", "Home Office"])

    region = rng.choice(regions, size=n, p=[0.3, 0.25, 0.25, 0.2])
    category = rng.choice(categories, size=n, p=[0.35, 0.25, 0.2, 0.2])
    segment = rng.choice(segments, size=n, p=[0.5, 0.3, 0.2])

    # Base price by category
    base_price = {"Electronics": 350.0, "Furniture": 280.0, "Office Supplies": 45.0, "Apparel": 65.0}
    cost_ratio = {"Electronics": 0.62, "Furniture": 0.58, "Office Supplies": 0.45, "Apparel": 0.50}
    unit_price = np.array([rng.normal(base_price[c], base_price[c] * 0.25) for c in category])
    unit_price = np.clip(unit_price, 5.0, 2500.0).round(2)

    quantity = rng.integers(1, 11, size=n)

    is_q4_2024 = np.array([(d >= q4_start) for d in order_dates])
    # Discounts: baseline 0-15%, Q4 2024: 15-35%
    discount_pct = np.where(
        is_q4_2024,
        rng.uniform(15.0, 35.0, size=n),
        rng.uniform(0.0, 15.0, size=n),
    ).round(1)
    # Shipping: baseline 5-25, Q4 2024: 10-45
    shipping_cost = np.where(
        is_q4_2024,
        rng.uniform(10.0, 45.0, size=n),
        rng.uniform(5.0, 25.0, size=n),
    ).round(2)
    # Returns: baseline ~5%, Q4 2024 ~15%
    return_prob = np.where(is_q4_2024, 0.15, 0.05)
    returned = (rng.random(n) < return_prob).astype(int)

    revenue = (quantity * unit_price * (1.0 - discount_pct / 100.0)).round(2)
    cogs = np.array([quantity[i] * unit_price[i] * cost_ratio[category[i]] for i in range(n)])
    profit = np.where(returned == 1, -cogs - shipping_cost, revenue - cogs - shipping_cost).round(2)

    customer_ids = rng.integers(1000, 9999, size=n)
    customer_id = np.array([f"CUST-{c:04d}" for c in customer_ids])
    emails = np.array([
        f"{rng.choice(FIRST)}.{rng.choice(LAST)}{int(c) % 997}@example.com".lower()
        for c in customer_ids
    ])
    order_id = np.array([f"ORD-{i + 1:06d}" for i in range(n)])

    df = pd.DataFrame({
        "order_id": order_id,
        "order_date": pd.to_datetime(order_dates),
        "region": region,
        "category": category,
        "segment": segment,
        "customer_id": customer_id,
        "customer_email": emails,  # PII-ish column for PII redaction demo
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_pct": discount_pct,
        "shipping_cost": shipping_cost,
        "returned": returned,
        "revenue": revenue,
        "profit": profit,
    })
    return df.sort_values("order_date").reset_index(drop=True)


def generate_saas(n: int, rng: np.random.Generator) -> pd.DataFrame:
    plans = np.array(["Basic", "Pro", "Enterprise"])
    plan = rng.choice(plans, size=n, p=[0.5, 0.32, 0.18])
    seg_map = {"Basic": "SMB", "Pro": "Mid-Market", "Enterprise": "Enterprise"}
    segment = np.array([seg_map[p] for p in plan])
    # Some cross-segment noise (10%): Pro sold to SMB etc. Keep mostly aligned.
    noise_idx = rng.choice(n, size=int(n * 0.08), replace=False)
    alt_segs = np.array(["SMB", "Mid-Market", "Enterprise"])
    segment[noise_idx] = rng.choice(alt_segs, size=len(noise_idx))

    base_mrr = {"Basic": 49.0, "Pro": 299.0, "Enterprise": 1499.0}
    seats = np.where(
        plan == "Basic", rng.integers(1, 11, size=n),
        np.where(plan == "Pro", rng.integers(5, 51, size=n), rng.integers(20, 501, size=n)),
    )
    mrr = np.array([
        round(base_mrr[plan[i]] + seats[i] * rng.uniform(2.0, 8.0) + rng.normal(0, base_mrr[plan[i]] * 0.08), 2)
        for i in range(n)
    ])
    mrr = np.clip(mrr, 10.0, None)

    # Churn: Basic ~22%, Pro ~10%, Enterprise ~4%
    churn_prob = np.where(plan == "Basic", 0.22, np.where(plan == "Pro", 0.10, 0.04))
    churned = (rng.random(n) < churn_prob).astype(int)

    start = date(2022, 1, 1)
    span = (date(2024, 12, 31) - start).days
    signup_dates = [start + timedelta(days=int(d)) for d in rng.integers(0, span + 1, size=n)]

    companies = [f"Acme-{rng.integers(100, 9999)} {'Labs' if rng.random() < 0.3 else 'Inc'}"
                 for _ in range(n)]

    df = pd.DataFrame({
        "subscription_id": [f"SUB-{i + 1:05d}" for i in range(n)],
        "customer": companies,
        "plan": plan,
        "segment": segment,
        "mrr": mrr,
        "churned": churned,
        "signup_date": pd.to_datetime(signup_dates),
        "seats": seats,
    })
    return df.sort_values("signup_date").reset_index(drop=True)


def generate_cloud_spend(n: int, rng: np.random.Generator) -> pd.DataFrame:
    services = np.array(["EC2", "S3", "RDS", "Lambda", "Redshift", "SageMaker"])
    teams = np.array(["Data", "Platform", "ML", "Backend"])
    envs = np.array(["prod", "staging", "dev"])
    service = rng.choice(services, size=n, p=[0.28, 0.18, 0.16, 0.14, 0.10, 0.14])
    team = rng.choice(teams, size=n, p=[0.3, 0.25, 0.2, 0.25])
    env = rng.choice(envs, size=n, p=[0.55, 0.2, 0.25])

    rate = {"EC2": 0.12, "S3": 0.023, "RDS": 0.18, "Lambda": 0.05, "Redshift": 0.35, "SageMaker": 0.9}
    usage_hours = np.clip(rng.normal(120, 80, size=n), 1, 720).round(1)
    cost = np.array([usage_hours[i] * rate[service[i]] * rng.uniform(0.85, 1.25) for i in range(n)]).round(2)

    start = date(2024, 1, 1)
    span = (date(2024, 12, 31) - start).days
    dates = [start + timedelta(days=int(d)) for d in rng.integers(0, span + 1, size=n)]

    df = pd.DataFrame({
        "service": service, "team": team, "env": env,
        "cost": cost, "usage_hours": usage_hours,
        "date": pd.to_datetime(dates),
    })
    # Intentional spike: SageMaker / ML / prod rows in Nov 2024 get 3-5x cost
    nov_mask = (df["date"] >= "2024-11-01") & (df["date"] <= "2024-11-30") & \
               (df["service"] == "SageMaker") & (df["team"] == "ML") & (df["env"] == "prod")
    spike_idx = df[nov_mask].sample(frac=0.7, random_state=DEFAULT_SEED).index
    df.loc[spike_idx, "cost"] = (df.loc[spike_idx, "cost"] * rng.uniform(3.0, 5.0, size=len(spike_idx))).round(2)
    df.loc[spike_idx, "usage_hours"] = (df.loc[spike_idx, "usage_hours"] * rng.uniform(1.5, 2.5, size=len(spike_idx))).round(1)
    return df.sort_values("date").reset_index(drop=True)


def generate_manufacturing(n: int, rng: np.random.Generator) -> pd.DataFrame:
    lines = np.array(["L1", "L2", "L3", "L4"])
    shifts = np.array(["Day", "Night"])
    line = rng.choice(lines, size=n)
    shift = rng.choice(shifts, size=n, p=[0.55, 0.45])

    start = date(2024, 1, 1)
    span = (date(2024, 12, 31) - start).days
    dates = [start + timedelta(days=int(d)) for d in rng.integers(0, span + 1, size=n)]
    dates_s = pd.to_datetime(dates)

    defect_rate = np.clip(rng.normal(2.0, 0.8, size=n), 0.2, 6.0).round(2)
    # Intentional outlier: L3 Night in Q3 2024 -> 6-9% defects
    q3_mask = [(d >= pd.Timestamp("2024-07-01") and d <= pd.Timestamp("2024-09-30")) for d in dates_s]
    spike = [(line[i] == "L3" and shift[i] == "Night" and q3_mask[i]) for i in range(n)]
    spike = np.array(spike)
    defect_rate[spike] = rng.uniform(6.0, 9.0, size=int(spike.sum())).round(2)

    throughput = np.clip(rng.normal(500, 120, size=n) - (defect_rate * 15), 100, 900).astype(int)
    downtime_min = np.clip(rng.normal(25, 18, size=n) + defect_rate * 6, 0, 240).astype(int)

    df = pd.DataFrame({
        "line": line, "shift": shift,
        "defect_rate": defect_rate, "throughput": throughput,
        "downtime_min": downtime_min, "date": dates_s,
    })
    return df.sort_values("date").reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-scale", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    s = args.rows_scale
    rng = _rng(args.seed)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[insightforge] seed={args.seed} rows_scale={s}")
    eco = generate_ecommerce(int(5000 * s), rng)
    saas = generate_saas(int(3000 * s), rng)
    cloud = generate_cloud_spend(int(4000 * s), rng)
    mfg = generate_manufacturing(int(3500 * s), rng)

    eco.to_excel(SAMPLE_DIR / "ecommerce.xlsx", index=False)
    eco.to_csv(SAMPLE_DIR / "ecommerce.csv", index=False)
    eco.to_parquet(SAMPLE_DIR / "ecommerce.parquet", index=False)
    saas.to_csv(SAMPLE_DIR / "saas.csv", index=False)
    cloud.to_json(SAMPLE_DIR / "cloud_spend.json", orient="records", date_format="iso")
    cloud.to_parquet(SAMPLE_DIR / "cloud_spend.parquet", index=False)
    mfg.to_parquet(SAMPLE_DIR / "manufacturing.parquet", index=False)
    mfg.to_csv(SAMPLE_DIR / "manufacturing.csv", index=False)

    # Summary + Q4 check
    q4 = eco[eco["order_date"] >= "2024-10-01"]
    pre = eco[(eco["order_date"] >= "2024-07-01") & (eco["order_date"] < "2024-10-01")]
    for name, df_ in [("ecommerce", eco), ("saas", saas), ("cloud_spend", cloud), ("manufacturing", mfg)]:
        print(f"  {name}: {len(df_)} rows")
    print(f"  ecommerce Q3 revenue={pre['revenue'].sum():,.0f} profit={pre['profit'].sum():,.0f} "
          f"avg_discount={pre['discount_pct'].mean():.1f}% return_rate={pre['returned'].mean():.1%}")
    print(f"  ecommerce Q4 revenue={q4['revenue'].sum():,.0f} profit={q4['profit'].sum():,.0f} "
          f"avg_discount={q4['discount_pct'].mean():.1f}% return_rate={q4['returned'].mean():.1%}")
    print(f"[insightforge] wrote 8 files to {SAMPLE_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/bin/sh
# Healthcheck: verifies data slice artifacts without needing the full stack.
set -eu
cd "$(dirname "$0")/.."
echo "== sample-data =="
ls sample-data/
echo "== row counts =="
python -c "import pandas as pd,json; print('ecommerce:',len(pd.read_parquet('sample-data/ecommerce.parquet'))); print('saas:',len(pd.read_csv('sample-data/saas.csv'))); print('cloud_spend:',len(pd.read_parquet('sample-data/cloud_spend.parquet'))); print('manufacturing:',len(pd.read_parquet('sample-data/manufacturing.parquet')))"
echo "== eval bank =="
python -c "import json; print(len(json.load(open('evals/eval_questions.json'))),'questions')"
echo "== demo contract =="
python tests/test_e2e_demo.py
echo "[healthcheck] OK"

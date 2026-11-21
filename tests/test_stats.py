"""Deterministic statistics tests (no network)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.statistics import (  # noqa: E402
    cohort,
    confidence,
    correlation,
    distribution,
    mean,
    median,
    outlier_iqr_zscore,
    pct_change,
    quantiles,
    regression,
    rolling_avg,
    segmentation,
    std,
    trend,
)


def test_mean_median_std():
    assert mean([1, 2, 3]) == 2.0
    assert median([3, 1, 2]) == 2.0
    assert median([1, 2, 3, 4]) == 2.5
    assert mean([]) is None
    assert abs((std([1, 2, 3, 4]) or 0) - 1.2909944487358056) < 1e-9


def test_pct_change():
    assert pct_change(100, 150) == 50.0
    assert pct_change(0, 5) is None


def test_distribution():
    d = distribution([1, 2, 3, 4], bins=2)
    assert sum(d["counts"]) == 4 and len(d["edges"]) == 3


def test_correlation():
    assert abs((correlation([1, 2, 3], [2, 4, 6]) or 0) - 1.0) < 1e-9
    assert correlation([1, 1, 1], [1, 2, 3]) is None


def test_quantiles_trend():
    q = quantiles([1, 2, 3, 4, 5])
    assert q["p50"] == 3
    assert trend([1, 2, 3])["direction"] == "up"
    assert trend([3, 2, 1])["direction"] == "down"


def test_rolling_outliers():
    assert rolling_avg([1, 2, 3], window=2) == [1.0, 1.5, 2.5]
    assert outlier_iqr_zscore([1, 2, 3, 100])["indices"] != []


def test_regression_confidence():
    r = regression([1, 2, 3], [2, 4, 6])
    assert abs(r["slope"] - 2.0) < 1e-9 and abs(r["r2"] - 1.0) < 1e-9
    c = confidence([1, 2, 3, 4, 5])
    assert c["low"] < c["mean"] < c["high"]


def test_cohort_segmentation():
    ch = cohort([10, 20, 30], ["a", "a", "b"])
    assert ch["a"]["count"] == 2 and ch["b"]["mean"] == 30
    seg = segmentation([10, 20, 30], ["a", "a", "b"])
    assert seg[0]["segment"] in ("a", "b")

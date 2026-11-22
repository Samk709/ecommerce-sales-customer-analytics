"""
Phase 4: EDA & Customer Intelligence Test Suite
Verifies mathematical integrity, data consistency, and business logic across all analytical modules.
"""

import os
import pytest
import pandas as pd
import numpy as np

EXPORTS_DIR = "data/exports"

def test_rfm_customer_count_and_revenue_integrity():
    """Verify RFM customer counts sum to 93,358, repeat buyers sum to 2,801, and revenue sums to R$ 13,221,498.11."""
    rfm_path = os.path.join(EXPORTS_DIR, "rfm_customer_segments.csv")
    assert os.path.exists(rfm_path), "rfm_customer_segments.csv does not exist"
    
    df = pd.read_csv(rfm_path)
    assert len(df) == 93358
    assert abs(df["monetary"].sum() - 13221498.11) <= 0.05
    assert (df["frequency"] >= 2).sum() == 2801
    
    summary_path = os.path.join(EXPORTS_DIR, "rfm_segment_summary.csv")
    assert os.path.exists(summary_path), "rfm_segment_summary.csv does not exist"
    
    summary = pd.read_csv(summary_path)
    assert summary["customer_count"].sum() == 93358
    assert summary["repeat_customers"].sum() == 2801
    assert abs(summary["total_revenue_brl"].sum() - 13221498.11) <= 0.05
    
    expected_segments = {"Top Value", "Mid Value", "Dormant", "Low Spend"}
    assert set(summary["segment"]) == expected_segments
    
    # Verify repeat buyer share calculations
    for _, row in summary.iterrows():
        expected_repeat_pct = round((row["repeat_customers"] / row["customer_count"]) * 100, 2)
        assert round(row["repeat_buyer_pct"], 2) == expected_repeat_pct

def test_cohort_retention_structure_and_bounds():
    """Verify cohort retention matrix structure, zero-value handling for observed periods, and bounded rates."""
    cohort_path = os.path.join(EXPORTS_DIR, "cohort_retention_matrix.csv")
    assert os.path.exists(cohort_path), "cohort_retention_matrix.csv does not exist"
    
    df = pd.read_csv(cohort_path, index_col=0)
    # Check that Month 0 is 100.0% for all cohorts
    assert (df["0"] == 100.0).all()
    
    # Check that observed subsequent months are between 0 and 100%
    subsequent = df.drop(columns=["0"])
    valid_rates = subsequent.dropna().values
    assert (valid_rates >= 0.0).all() and (valid_rates <= 100.0).all()
    
    # Check that observed zero months contain 0.0 (not null)
    # E.g., for early cohorts (2016-09 or 2016-10), there are observed months with 0.0
    assert (subsequent == 0.0).any().any()
    
    # Average Month 1 retention across cohorts should be structurally low (< 1.0%)
    m1_rates = df.loc["2017-01":"2017-12", "1"].dropna()
    assert m1_rates.mean() < 1.0

def test_clv_metrics_consistency():
    """Verify historical and segment-level Customer Lifetime Value consistency."""
    rfm_path = os.path.join(EXPORTS_DIR, "rfm_customer_segments.csv")
    df = pd.read_csv(rfm_path)
    
    historical_clv = df["monetary"].sum() / len(df)
    assert round(historical_clv, 2) == 141.62
    
    repeat_clv = df[df["frequency"] >= 2]["monetary"].sum() / len(df[df["frequency"] >= 2])
    onetime_clv = df[df["frequency"] == 1]["monetary"].sum() / len(df[df["frequency"] == 1])
    
    assert round(repeat_clv, 2) == 260.05
    assert round(onetime_clv, 2) == 137.96
    assert repeat_clv > onetime_clv

def test_product_pareto_integrity():
    """Verify product Pareto calculation, 80% cutoff, and cumulative revenue reach."""
    pareto_path = os.path.join(EXPORTS_DIR, "pareto_product_summary.csv")
    assert os.path.exists(pareto_path), "pareto_product_summary.csv does not exist"
    
    df = pd.read_csv(pareto_path)
    assert len(df) == 32216
    assert abs(df["cum_revenue_pct"].iloc[-1] - 100.0) <= 0.01
    
    # Check 80% cutoff products
    cutoff_80 = len(df[df["cum_revenue_pct"] <= 80.0]) + 1
    assert cutoff_80 == 8352
    assert round((cutoff_80 / len(df)) * 100, 2) == 25.93

def test_delivery_csat_delay_summary():
    """Verify delivery delay bucket review counts and satisfaction degradation."""
    csat_path = os.path.join(EXPORTS_DIR, "delivery_csat_delay_summary.csv")
    assert os.path.exists(csat_path), "delivery_csat_delay_summary.csv does not exist"
    
    df = pd.read_csv(csat_path)
    total_reviews = df["review_count"].sum()
    assert total_reviews == 96353
    
    # On-time score must be higher than minor delay score
    ontime_score = df.iloc[0]["avg_review_score"]
    minor_delay_score = df.iloc[1]["avg_review_score"]
    assert ontime_score > minor_delay_score
    assert round(ontime_score, 2) == 4.29
    
    # Late reviews sum to 6,409
    late_reviews = df.iloc[1:]["review_count"].sum()
    assert late_reviews == 6409

def test_category_profitability_summary():
    """Verify macro category profitability reconciliation against Phase 3 totals."""
    cat_path = os.path.join(EXPORTS_DIR, "category_profitability_summary.csv")
    assert os.path.exists(cat_path), "category_profitability_summary.csv does not exist"
    
    df = pd.read_csv(cat_path)
    assert len(df) == 11
    
    total_revenue = df["total_revenue_brl"].sum()
    total_cogs = df["assumed_cogs_brl"].sum()
    total_gp = df["assumed_gross_profit_brl"].sum()
    
    assert abs(total_revenue - 13221498.11) <= 0.05
    assert abs(total_cogs - 7832679.15) <= 0.05
    assert abs(total_gp - 5388818.98) <= 0.05
    assert round((total_gp / total_revenue) * 100, 2) == 40.76

def test_daily_sales_forecast_integrity():
    """Verify that daily sales forecast CSV contains historical and future dates with valid values."""
    fc_path = os.path.join(EXPORTS_DIR, "daily_sales_forecast.csv")
    assert os.path.exists(fc_path), "daily_sales_forecast.csv does not exist"
    
    df = pd.read_csv(fc_path)
    assert "actual_revenue_brl" in df.columns
    assert "future_forecast_brl" in df.columns
    
    # Future forecast must have 30 non-null values
    future_vals = df["future_forecast_brl"].dropna()
    assert len(future_vals) == 30
    assert (future_vals > 0).all()

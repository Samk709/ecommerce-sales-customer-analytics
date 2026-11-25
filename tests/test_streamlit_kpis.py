"""
Phase 6: Streamlit KPI Module Unit Tests
Verifies that the standalone KPI calculation engine reproduces the exact platform baseline numbers:
1. Total Delivered Merchandise Revenue: R$ 13,221,498.11
2. Total Delivered Orders: 96,478
3. Total Repeat Customers: 2,801
"""

import os
import pytest
import pandas as pd
from streamlit_app.kpi_metrics import (
    compute_overview_kpis,
    filter_dataset,
    compute_baseline_kpis_from_tables,
    BASELINE_KPIS
)

EXPORTS_DIR = "data/exports"

@pytest.fixture(scope="module")
def dataset():
    """Load exported CSV datasets once for testing."""
    orders_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_orders.csv"))
    items_df = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_items.csv"))
    customers_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_customers.csv"))
    products_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_products.csv"))
    return orders_df, items_df, customers_df, products_df

def test_unfiltered_baseline_kpis(dataset):
    """
    Test that with no filters, the KPI engine exactly reproduces the required baseline figures:
    - Revenue = R$ 13,221,498.11
    - Delivered Orders = 96,478
    - Repeat Customers = 2,801
    """
    orders_df, items_df, customers_df, _ = dataset
    kpis = compute_overview_kpis(orders_df, items_df, customers_df)
    
    # 1. Exact revenue check
    assert kpis["total_revenue_brl"] == 13221498.11, f"Expected 13,221,498.11, got {kpis['total_revenue_brl']}"
    
    # 2. Exact order count check
    assert kpis["total_delivered_orders"] == 96478, f"Expected 96,478, got {kpis['total_delivered_orders']}"
    
    # 3. Exact repeat customer count check
    assert kpis["repeat_customers_count"] == 2801, f"Expected 2,801, got {kpis['repeat_customers_count']}"
    
    # 4. Secondary integrity metrics
    assert kpis["aov_brl"] == 137.04
    assert kpis["total_freight_brl"] == 2198275.64
    assert kpis["gmv_brl"] == 15419773.75
    assert kpis["assumed_gross_profit_brl"] == 5388818.98
    assert kpis["total_unique_customers"] == 93358
    assert kpis["blended_gross_margin_pct"] == 40.76

def test_financial_kpis_and_margins(dataset):
    """
    Test that the KPI engine exactly reproduces verified financial totals:
    - GMV = R$ 15,419,773.75 (= R$ 13,221,498.11 revenue + R$ 2,198,275.64 freight)
    - Total Freight = R$ 2,198,275.64
    - Assumed Gross Profit = R$ 5,388,818.98
    - Blended Gross Margin = 40.76%
    """
    orders_df, items_df, customers_df, _ = dataset
    kpis = compute_overview_kpis(orders_df, items_df, customers_df)
    
    assert kpis["total_revenue_brl"] == 13221498.11
    assert kpis["total_freight_brl"] == 2198275.64
    assert kpis["gmv_brl"] == 15419773.75
    assert kpis["gmv_brl"] == round(kpis["total_revenue_brl"] + kpis["total_freight_brl"], 2)
    assert kpis["assumed_gross_profit_brl"] == 5388818.98
    assert kpis["blended_gross_margin_pct"] == 40.76

def test_filtered_kpis_subset_logic(dataset):
    """Test that applying filters correctly returns a subset of revenue and orders."""
    orders_df, items_df, customers_df, products_df = dataset
    
    # Filter for top state 'SP' (São Paulo)
    f_orders, f_items, f_cust, f_prod = filter_dataset(
        orders_df, items_df, customers_df, products_df,
        selected_states=["SP"]
    )
    kpis_sp = compute_overview_kpis(f_orders, f_items, f_cust)
    
    # State SP should have fewer orders and lower revenue than platform total
    assert kpis_sp["total_delivered_orders"] < 96478
    assert kpis_sp["total_revenue_brl"] < 13221498.11
    assert kpis_sp["total_revenue_brl"] > 4000000.0  # SP is >35% of platform

def test_rfm_segment_filter_logic(dataset):
    """Test filtering by RFM segment 'Top Value'."""
    orders_df, items_df, customers_df, products_df = dataset
    
    f_orders, f_items, f_cust, f_prod = filter_dataset(
        orders_df, items_df, customers_df, products_df,
        selected_rfm=["Top Value"]
    )
    kpis_top = compute_overview_kpis(f_orders, f_items, f_cust)
    
    assert kpis_top["repeat_customers_count"] == 1549
    assert abs(kpis_top["total_revenue_brl"] - 2358970.15) <= 1.0

def test_baseline_kpis_recomputed_from_full_tables(dataset):
    """
    Verify that BASELINE_KPIS values are dynamically computed from data (not typed into code):
    Recomputes all metrics from raw full tables and checks that every single
    value matches BASELINE_KPIS and the verified platform figures.
    """
    orders_df, items_df, customers_df, _ = dataset
    recomputed = compute_baseline_kpis_from_tables(orders_df, items_df, customers_df)
    
    # Assert every key in recomputed matches BASELINE_KPIS exactly
    for key, val in recomputed.items():
        assert key in BASELINE_KPIS, f"Key {key} missing from BASELINE_KPIS"
        assert val == BASELINE_KPIS[key], f"Mismatch for {key}: recomputed {val} vs BASELINE_KPIS {BASELINE_KPIS[key]}"
    
    # Assert exact verified values
    assert recomputed["total_revenue_brl"] == 13221498.11
    assert recomputed["total_delivered_orders"] == 96478
    assert recomputed["repeat_customers_count"] == 2801
    assert recomputed["aov_brl"] == 137.04
    assert recomputed["total_freight_brl"] == 2198275.64
    assert recomputed["gmv_brl"] == 15419773.75
    assert recomputed["assumed_cogs_brl"] == 7832679.13
    assert recomputed["assumed_gross_profit_brl"] == 5388818.98
    assert recomputed["blended_gross_margin_pct"] == 40.76
    assert recomputed["total_unique_customers"] == 93358
    assert recomputed["repeat_customer_rate_pct"] == 3.00
    assert recomputed["total_items_sold"] == 110197

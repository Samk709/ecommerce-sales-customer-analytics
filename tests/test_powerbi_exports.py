"""
Phase 5: Power BI Star Schema Integrity & Reconciliation Test Suite
Verifies existence, row counts, foreign key integrity, and financial reconciliation
of exported Star Schema dimension and fact tables.
"""

import os
import pytest
import pandas as pd
import numpy as np

EXPORTS_DIR = "data/exports"

def test_powerbi_csv_existence():
    """Verify that all 8 Star Schema tables exist in data/exports/."""
    expected_files = [
        "dim_orders.csv",
        "dim_customers.csv",
        "dim_products.csv",
        "dim_sellers.csv",
        "dim_calendar.csv",
        "fact_order_items.csv",
        "fact_order_payments.csv",
        "fact_order_reviews.csv"
    ]
    for fname in expected_files:
        path = os.path.join(EXPORTS_DIR, fname)
        assert os.path.exists(path), f"Required Star Schema table missing: {fname}"

def test_powerbi_table_row_counts():
    """Verify exact row counts for all Star Schema tables matching warehouse counts."""
    expected_counts = {
        "dim_orders.csv": 99441,
        "dim_customers.csv": 99441,
        "dim_products.csv": 32951,
        "dim_sellers.csv": 3095,
        "dim_calendar.csv": 1096,  # 366 (2016 leap) + 365 (2017) + 365 (2018)
        "fact_order_items.csv": 112650,
        "fact_order_payments.csv": 103886,
        "fact_order_reviews.csv": 99224
    }
    for fname, count in expected_counts.items():
        path = os.path.join(EXPORTS_DIR, fname)
        df = pd.read_csv(path)
        assert len(df) == count, f"Row count mismatch in {fname}: got {len(df)}, expected {count}"

def test_powerbi_referential_integrity():
    """Verify that there are zero orphaned foreign keys in the fact tables."""
    orders_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_orders.csv"), usecols=["order_id", "customer_id"])
    customers_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_customers.csv"), usecols=["customer_id"])
    products_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_products.csv"), usecols=["product_id"])
    sellers_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_sellers.csv"), usecols=["seller_id"])
    items_df = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_items.csv"), usecols=["order_id", "product_id", "seller_id"])
    payments_df = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_payments.csv"), usecols=["order_id"])
    reviews_df = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_reviews.csv"), usecols=["order_id"])

    order_ids = set(orders_df["order_id"])
    customer_ids = set(customers_df["customer_id"])
    product_ids = set(products_df["product_id"])
    seller_ids = set(sellers_df["seller_id"])

    # 1. Orders -> Customers
    assert set(orders_df["customer_id"]).issubset(customer_ids), "Orphan customer_ids in dim_orders"
    # 2. Items -> Orders, Products, Sellers
    assert set(items_df["order_id"]).issubset(order_ids), "Orphan order_ids in fact_order_items"
    assert set(items_df["product_id"]).issubset(product_ids), "Orphan product_ids in fact_order_items"
    assert set(items_df["seller_id"]).issubset(seller_ids), "Orphan seller_ids in fact_order_items"
    # 3. Payments -> Orders
    assert set(payments_df["order_id"]).issubset(order_ids), "Orphan order_ids in fact_order_payments"
    # 4. Reviews -> Orders
    assert set(reviews_df["order_id"]).issubset(order_ids), "Orphan order_ids in fact_order_reviews"

def test_powerbi_financial_reconciliation():
    """Verify that delivered revenue, freight, COGS, and GP in exported fact tables match warehouse totals."""
    orders_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_orders.csv"), usecols=["order_id", "order_status"])
    items_df = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_items.csv"))

    delivered_orders = set(orders_df[orders_df["order_status"] == "delivered"]["order_id"])
    assert len(delivered_orders) == 96478

    delivered_items = items_df[items_df["order_id"].isin(delivered_orders)]
    assert len(delivered_items) == 110197

    # Total Delivered Item Revenue: R$ 13,221,498.11
    tot_rev = delivered_items["price"].sum()
    assert abs(tot_rev - 13221498.11) <= 0.05, f"Revenue mismatch: {tot_rev}"

    # Total Delivered Freight: R$ 2,198,275.64 (reconciles with Query 1 and Query 9)
    tot_freight = delivered_items["freight_value"].sum()
    assert abs(tot_freight - 2198275.64) <= 0.05, f"Freight mismatch: {tot_freight}"

    # Assumed COGS and GP
    tot_cogs = delivered_items["assumed_cogs_brl"].sum()
    tot_gp = delivered_items["assumed_gross_profit_brl"].sum()
    assert abs(tot_cogs - 7832679.15) <= 1.0, f"COGS mismatch: {tot_cogs}"
    assert abs(tot_gp - 5388818.98) <= 1.0, f"GP mismatch: {tot_gp}"

def test_powerbi_customer_repeat_and_rfm_enrichment():
    """Verify customer dimension RFM segmentation and repeat customer flags."""
    cust_df = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_customers.csv"))
    
    # Repeat buyers check (unique customers with >=2 delivered orders = 2,801)
    repeat_uniques = cust_df[cust_df["is_repeat_customer"] == 1]["customer_unique_id"].nunique()
    assert repeat_uniques == 2801

    # RFM Segment integrity
    rfm_segments = set(cust_df["rfm_segment"].unique())
    assert {"Top Value", "Mid Value", "Dormant", "Low Spend"}.issubset(rfm_segments)

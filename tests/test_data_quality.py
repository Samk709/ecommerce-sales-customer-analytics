"""
Data Quality and Integrity Test Suite
Verifies that all preprocessed datasets meet strict relational integrity,
domain bounds, and schema requirements.
"""

import os
import pandas as pd
import pytest
from src.config import PROCESSED_DATA_DIR

PROCESSED_FILES = [
    "dim_orders.csv",
    "fact_order_items.csv",
    "fact_order_payments.csv",
    "fact_order_reviews.csv",
    "dim_products.csv",
    "dim_customers.csv",
    "dim_sellers.csv",
    "dim_geolocation.csv",
    "dim_category_translation.csv"
]

@pytest.fixture(scope="session")
def processed_dfs():
    dfs = {}
    for f in PROCESSED_FILES:
        path = os.path.join(PROCESSED_DATA_DIR, f)
        assert os.path.exists(path), f"Processed file missing: {path}"
        dfs[f] = pd.read_csv(path)
    return dfs

def test_files_exist_and_non_empty(processed_dfs):
    """Ensure all processed CSV files exist and contain records."""
    for filename, df in processed_dfs.items():
        assert len(df) > 0, f"{filename} is empty!"

def test_primary_key_uniqueness(processed_dfs):
    """Verify primary keys are strictly unique across dimensional and fact entities."""
    # Orders
    orders_df = processed_dfs["dim_orders.csv"]
    assert orders_df["order_id"].is_unique, "Duplicate order_id found in dim_orders"

    # Order Items (Composite Key)
    items_df = processed_dfs["fact_order_items.csv"]
    item_key_dups = items_df.duplicated(subset=["order_id", "order_item_id"]).sum()
    assert item_key_dups == 0, f"Duplicate composite key in fact_order_items: {item_key_dups}"

    # Payments (Composite Key)
    payments_df = processed_dfs["fact_order_payments.csv"]
    payment_key_dups = payments_df.duplicated(subset=["order_id", "payment_sequential"]).sum()
    assert payment_key_dups == 0, f"Duplicate composite key in fact_order_payments: {payment_key_dups}"

    # Reviews (Surrogate Key)
    reviews_df = processed_dfs["fact_order_reviews.csv"]
    assert reviews_df["review_surrogate_id"].is_unique, "Duplicate surrogate ID in fact_order_reviews"

    # Products
    products_df = processed_dfs["dim_products.csv"]
    assert products_df["product_id"].is_unique, "Duplicate product_id in dim_products"

    # Customers
    customers_df = processed_dfs["dim_customers.csv"]
    assert customers_df["customer_id"].is_unique, "Duplicate customer_id in dim_customers"

    # Sellers
    sellers_df = processed_dfs["dim_sellers.csv"]
    assert sellers_df["seller_id"].is_unique, "Duplicate seller_id in dim_sellers"

    # Geolocation (Deduplicated Zip Prefix)
    geo_df = processed_dfs["dim_geolocation.csv"]
    assert geo_df["geolocation_zip_code_prefix"].is_unique, "Duplicate zip code prefix in dim_geolocation"

def test_numeric_business_rules(processed_dfs):
    """Verify prices, freights, and scores adhere to positive ranges."""
    items_df = processed_dfs["fact_order_items.csv"]
    assert (items_df["price"] > 0).all(), "Found item prices <= 0"
    assert (items_df["freight_value"] >= 0).all(), "Found freight values < 0"

    reviews_df = processed_dfs["fact_order_reviews.csv"]
    assert reviews_df["review_score"].between(1, 5).all(), "Review scores outside [1, 5] range"

def test_financial_margin_assumptions(processed_dfs):
    """Verify that every product has a valid category group and financial rates."""
    products_df = processed_dfs["dim_products.csv"]
    assert not products_df["category_group"].isna().any(), "Found products with unmapped category group"
    assert products_df["assumed_cogs_rate"].between(0.1, 0.95).all(), "COGS rate out of expected bounds"
    assert products_df["assumed_gross_margin_rate"].between(0.05, 0.90).all(), "Margin rate out of bounds"
    # Ensure sum of COGS + Margin equals 1.0 (within float precision)
    sum_rates = products_df["assumed_cogs_rate"] + products_df["assumed_gross_margin_rate"]
    assert (sum_rates.round(2) == 1.0).all(), "COGS + Gross Margin rates do not sum to 1.0"

def test_geolocation_coordinate_bounds(processed_dfs):
    """Verify that all deduplicated coordinates fall within Brazilian territory bounds."""
    geo_df = processed_dfs["dim_geolocation.csv"]
    assert geo_df["geolocation_lat"].between(-35.0, 6.0).all(), "Latitude outside Brazilian bounds"
    assert geo_df["geolocation_lng"].between(-75.0, -33.0).all(), "Longitude outside Brazilian bounds"

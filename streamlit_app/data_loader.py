"""
==============================================================================
Data Loading & Caching Engine for Streamlit Application
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Pandas, PyArrow

Description:
High-performance cached data access layer. Reads from optimized Parquet files
with columnar loading and compact dtypes for sub-second execution, with fallback
to CSV.
==============================================================================
"""

import os
import streamlit as st
import pandas as pd

# Path to analytical data warehouse
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORTS_DIR = os.path.join(BASE_DIR, "data", "exports")

def _load_table(filename_base: str, usecols: list = None, dtypes: dict = None) -> pd.DataFrame:
    """Helper to load Parquet if available, falling back to CSV."""
    parquet_path = os.path.join(EXPORTS_DIR, f"{filename_base}.parquet")
    csv_path = os.path.join(EXPORTS_DIR, f"{filename_base}.csv")
    
    if os.path.exists(parquet_path):
        if usecols:
            # Only read columns that exist in the parquet file
            return pd.read_parquet(parquet_path, columns=usecols)
        return pd.read_parquet(parquet_path)
    elif os.path.exists(csv_path):
        if usecols:
            return pd.read_csv(csv_path, usecols=usecols, dtype=dtypes)
        return pd.read_csv(csv_path, dtype=dtypes)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_core_dimensions():
    """Load core dimensional and fact tables with only required columns and compact dtypes."""
    orders_cols = [
        "order_id", "customer_id", "order_status", "order_purchase_date",
        "is_delayed", "delivery_lead_time_days", "delivery_delay_days"
    ]
    items_cols = [
        "order_id", "product_id", "price", "freight_value", "assumed_cogs_brl", "assumed_gross_profit_brl"
    ]
    cust_cols = [
        "customer_id", "customer_unique_id", "customer_state", "rfm_segment", "is_repeat_customer"
    ]
    prod_cols = [
        "product_id", "category_group"
    ]

    orders_df = _load_table("dim_orders", usecols=orders_cols)
    items_df = _load_table("fact_order_items", usecols=items_cols)
    customers_df = _load_table("dim_customers", usecols=cust_cols)
    products_df = _load_table("dim_products", usecols=prod_cols)

    # Convert date strings to date objects if not already
    if not orders_df.empty:
        if not pd.api.types.is_datetime64_any_dtype(orders_df["order_purchase_date"]):
            orders_df["order_purchase_date"] = pd.to_datetime(orders_df["order_purchase_date"]).dt.date
        if "purchase_year_month" not in orders_df.columns:
            orders_df["purchase_year_month"] = pd.to_datetime(orders_df["order_purchase_date"].astype(str)).dt.strftime("%Y-%m")

    return orders_df, items_df, customers_df, products_df

# Pre-Aggregated Summary Loaders for Sub-Second Unfiltered Rendering

@st.cache_data(show_spinner=False)
def load_overview_monthly_trend() -> pd.DataFrame:
    """Load pre-aggregated monthly delivered sales and MoM growth."""
    return _load_table("overview_monthly_trend")

@st.cache_data(show_spinner=False)
def load_overview_state_summary() -> pd.DataFrame:
    """Load pre-aggregated customer state revenue and order volume."""
    return _load_table("overview_state_summary")

@st.cache_data(show_spinner=False)
def load_products_category_summary() -> pd.DataFrame:
    """Load pre-aggregated macro category sales and profit breakdown."""
    return _load_table("products_category_summary")

@st.cache_data(show_spinner=False)
def load_products_top20_summary() -> pd.DataFrame:
    """Load pre-aggregated top 20 best-selling SKUs."""
    return _load_table("products_top20_summary")

@st.cache_data(show_spinner=False)
def load_delivery_delay_daily() -> pd.DataFrame:
    """Load pre-aggregated daily delay vs CSAT rating scatter points."""
    return _load_table("delivery_delay_daily")

@st.cache_data(show_spinner=False)
def load_lead_time_distribution() -> pd.DataFrame:
    """Load pre-aggregated lead time days histogram bins."""
    return _load_table("lead_time_distribution")

# Standard Analytical Summary Loaders

@st.cache_data(show_spinner=False)
def load_rfm_summary():
    """Load pre-aggregated RFM customer segment summary."""
    return _load_table("rfm_segment_summary")

@st.cache_data(show_spinner=False)
def load_cohort_retention():
    """Load monthly cohort retention matrix."""
    path = os.path.join(EXPORTS_DIR, "cohort_retention_matrix.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_pareto_summary():
    """Load product portfolio Pareto distribution."""
    return _load_table("pareto_product_summary")

@st.cache_data(show_spinner=False)
def load_category_profitability():
    """Load macro category profitability summary."""
    return _load_table("category_profitability_summary")

@st.cache_data(show_spinner=False)
def load_delivery_csat_summary():
    """Load delivery delay vs CSAT score summary."""
    return _load_table("delivery_csat_delay_summary")

@st.cache_data(show_spinner=False)
def load_order_reviews():
    """Load fact order reviews table."""
    return _load_table("fact_order_reviews", usecols=["order_id", "review_score"])

@st.cache_data(show_spinner=False)
def load_sales_forecast():
    """Load 30-day Holt-Winters time-series sales forecast."""
    df = _load_table("daily_sales_forecast")
    if not df.empty and "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    return df

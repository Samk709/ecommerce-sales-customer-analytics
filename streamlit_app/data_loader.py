"""
==============================================================================
Data Loading & Caching Engine for Streamlit Application
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Pandas

Description:
Reads exclusively from data/exports/ CSV files using @st.cache_data for instant,
zero-database cloud deployment.
==============================================================================
"""

import os
import streamlit as st
import pandas as pd

# Path to pre-exported CSV warehouse
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORTS_DIR = os.path.join(BASE_DIR, "data", "exports")

@st.cache_data(show_spinner=False)
def load_core_dimensions():
    """Load core dimensional and fact tables required for interactive slicing."""
    orders_path = os.path.join(EXPORTS_DIR, "dim_orders.csv")
    items_path = os.path.join(EXPORTS_DIR, "fact_order_items.csv")
    customers_path = os.path.join(EXPORTS_DIR, "dim_customers.csv")
    products_path = os.path.join(EXPORTS_DIR, "dim_products.csv")

    orders_df = pd.read_csv(orders_path)
    items_df = pd.read_csv(items_path)
    customers_df = pd.read_csv(customers_path)
    products_df = pd.read_csv(products_path)

    # Convert date strings to datetime / date objects for smooth filtering
    orders_df["order_purchase_date"] = pd.to_datetime(orders_df["order_purchase_date"]).dt.date
    orders_df["purchase_year_month"] = pd.to_datetime(orders_df["order_purchase_date"]).dt.strftime("%Y-%m")

    return orders_df, items_df, customers_df, products_df

@st.cache_data(show_spinner=False)
def load_rfm_summary():
    """Load pre-aggregated RFM customer segment summary."""
    path = os.path.join(EXPORTS_DIR, "rfm_segment_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

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
    path = os.path.join(EXPORTS_DIR, "pareto_product_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_category_profitability():
    """Load macro category profitability summary."""
    path = os.path.join(EXPORTS_DIR, "category_profitability_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_delivery_csat_summary():
    """Load delivery delay vs CSAT score summary."""
    path = os.path.join(EXPORTS_DIR, "delivery_csat_delay_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_order_reviews():
    """Load fact order reviews table."""
    path = os.path.join(EXPORTS_DIR, "fact_order_reviews.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_sales_forecast():
    """Load 30-day Holt-Winters time-series sales forecast."""
    path = os.path.join(EXPORTS_DIR, "daily_sales_forecast.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
        return df
    return pd.DataFrame()

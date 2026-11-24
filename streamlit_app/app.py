"""
==============================================================================
E-Commerce Sales & Customer Intelligence Analytics Platform
Main Streamlit Application Entrypoint
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Pandas, Plotly

Description:
Zero-database interactive executive dashboard reading directly from pre-exported
CSVs in data/exports/. Features multi-dimensional slicing, dynamic Plotly charts,
and pure-Python KPI evaluation.
==============================================================================
"""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import datetime
from streamlit_app.components import inject_custom_css, render_header, render_footer
from streamlit_app.data_loader import load_core_dimensions
from streamlit_app.kpi_metrics import filter_dataset
from streamlit_app.views.overview import render_overview_view
from streamlit_app.views.products import render_products_view
from streamlit_app.views.customers import render_customers_view
from streamlit_app.views.delivery import render_delivery_view
from streamlit_app.views.forecast import render_forecast_view

# 1. Page Configuration
st.set_page_config(
    page_title="E-Commerce Sales & Customer Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Corporate Theme CSS
inject_custom_css()

# 3. Load Core Data with Subtle Loading Feedback
with st.spinner("Loading analytical data..."):
    orders_df, items_df, customers_df, products_df = load_core_dimensions()

# 4. Sidebar Controls & Multi-Dimensional Filters
st.sidebar.markdown(
    """
    <div style="padding: 10px 0 16px 0;">
        <h2 style="color: #1B2A4A; margin: 0; font-size: 1.30rem; font-weight: 800;">🛒 Olist Analytics</h2>
        <span style="color: #64748B; font-size: 0.78rem; font-weight: 600;">Executive Intelligence & Strategy</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### 🧭 Navigation")

# Support URL query parameter for page navigation
page_mapping = {
    "overview": "🏠 Executive Overview",
    "products": "📦 Products & Categories",
    "customers": "👥 Customers & Retention",
    "delivery": "🚚 Logistics SLA & CSAT",
    "forecast": "📈 Sales Forecast"
}
nav_options = [
    "🏠 Executive Overview",
    "📦 Products & Categories",
    "👥 Customers & Retention",
    "🚚 Logistics SLA & CSAT",
    "📈 Sales Forecast"
]
query_page = str(st.query_params.get("page", "")).lower()
default_nav_idx = 0
for idx, (k, v) in enumerate(page_mapping.items()):
    if query_page == k:
        default_nav_idx = idx
        break

nav_selection = st.sidebar.radio(
    "Select Report Page:",
    nav_options,
    index=default_nav_idx,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Global Slicers & Filters")

# Filter: Date Range
min_date = orders_df["order_purchase_date"].min()
max_date = orders_df["order_purchase_date"].max()

date_selection = st.sidebar.date_input(
    "Purchase Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_date, end_date = date_selection
else:
    start_date, end_date = min_date, max_date

# Filter: Macro Category Groups
all_categories = sorted(products_df["category_group"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Macro Category Group",
    options=all_categories,
    default=all_categories
)

# Filter: Customer States
all_states = sorted(customers_df["customer_state"].dropna().unique())
query_state = str(st.query_params.get("state", "")).upper()
default_states = [query_state] if query_state in all_states else all_states

selected_states = st.sidebar.multiselect(
    "Customer State (Federation)",
    options=all_states,
    default=default_states
)

# Filter: RFM Segments
all_rfm = ["Top Value", "Mid Value", "Dormant", "Low Spend"]
selected_rfm = st.sidebar.multiselect(
    "RFM Customer Segment",
    options=all_rfm,
    default=all_rfm
)

# Filter Reset Button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.query_params.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("E-Commerce Analytics Platform | Stack: Python, MySQL 8.0, Power BI, Streamlit")

# 5. Apply Filtering Engine
is_filtered = not (
    start_date == min_date and
    end_date == max_date and
    len(selected_categories) == len(all_categories) and
    len(selected_states) == len(all_states) and
    len(selected_rfm) == len(all_rfm)
)

f_orders, f_items, f_cust, f_prod = filter_dataset(
    orders_df=orders_df,
    items_df=items_df,
    customers_df=customers_df,
    products_df=products_df,
    start_date=start_date,
    end_date=end_date,
    selected_categories=selected_categories if len(selected_categories) < len(all_categories) else None,
    selected_states=selected_states if len(selected_states) < len(all_states) else None,
    selected_rfm=selected_rfm if len(selected_rfm) < len(all_rfm) else None
)

# 6. Render Executive Top Header
subtitle_map = {
    "🏠 Executive Overview": "Executive Sales & Commercial Performance Overview",
    "📦 Products & Categories": "Catalog Margin Analysis & 80/20 Pareto Distribution",
    "👥 Customers & Retention": "Customer Loyalty Economics, RFM Segments & Cohort Decay",
    "🚚 Logistics SLA & CSAT": "Fulfillment Lead Time, SLA Breach Penalty & Review Ratings",
    "📈 Sales Forecast": "Time-Series Cyclicality & 30-Day Forward Sales Projection"
}
render_header(subtitle=subtitle_map.get(nav_selection, "Executive Sales & Customer Intelligence Analytics Platform"))

# 7. Page Routing
if nav_selection == "🏠 Executive Overview":
    render_overview_view(f_orders, f_items, f_cust, is_filtered)
elif nav_selection == "📦 Products & Categories":
    render_products_view(f_orders, f_items, f_prod)
elif nav_selection == "👥 Customers & Retention":
    render_customers_view(f_cust, f_orders, f_items)
elif nav_selection == "🚚 Logistics SLA & CSAT":
    render_delivery_view(f_orders)
elif nav_selection == "📈 Sales Forecast":
    render_forecast_view()

# 8. Render Executive Footer
render_footer()

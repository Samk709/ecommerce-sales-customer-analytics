"""
==============================================================================
App Data & Parquet Pre-Aggregation Generator
==============================================================================
Generates compact, high-performance Parquet files and pre-aggregated summaries
for the Streamlit application from data/exports/ CSV files.
==============================================================================
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORTS_DIR = os.path.join(BASE_DIR, "data", "exports")

def generate_all():
    print(f"Reading from {EXPORTS_DIR}...")

    # 1. Load CSVs with required columns
    orders = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_orders.csv"), usecols=[
        "order_id", "customer_id", "order_status", "order_purchase_date",
        "is_delayed", "delivery_lead_time_days", "delivery_delay_days"
    ])
    orders["order_purchase_date"] = pd.to_datetime(orders["order_purchase_date"]).dt.date
    orders["purchase_year_month"] = pd.to_datetime(orders["order_purchase_date"].astype(str)).dt.strftime("%Y-%m")
    orders["order_status"] = orders["order_status"].astype("category")
    orders["purchase_year_month"] = orders["purchase_year_month"].astype("category")
    orders["is_delayed"] = orders["is_delayed"].astype("float32")
    orders["delivery_lead_time_days"] = orders["delivery_lead_time_days"].astype("float32")
    orders["delivery_delay_days"] = orders["delivery_delay_days"].astype("float32")

    items = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_items.csv"), usecols=[
        "order_id", "product_id", "price", "freight_value", "assumed_cogs_brl", "assumed_gross_profit_brl"
    ])
    for col in ["price", "freight_value", "assumed_cogs_brl", "assumed_gross_profit_brl"]:
        items[col] = items[col].astype("float64")

    customers = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_customers.csv"), usecols=[
        "customer_id", "customer_unique_id", "customer_state", "rfm_segment", "is_repeat_customer"
    ])
    customers["customer_state"] = customers["customer_state"].astype("category")
    customers["rfm_segment"] = customers["rfm_segment"].astype("category")
    customers["is_repeat_customer"] = customers["is_repeat_customer"].astype("int8")

    products = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_products.csv"), usecols=[
        "product_id", "category_group", "product_category_name_english"
    ])
    products["category_group"] = products["category_group"].astype("category")

    reviews = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_order_reviews.csv"), usecols=[
        "order_id", "review_score"
    ])
    reviews["review_score"] = reviews["review_score"].astype("int8")

    # 2. Write core Parquet tables
    orders.to_parquet(os.path.join(EXPORTS_DIR, "dim_orders.parquet"), index=False)
    items.to_parquet(os.path.join(EXPORTS_DIR, "fact_order_items.parquet"), index=False)
    customers.to_parquet(os.path.join(EXPORTS_DIR, "dim_customers.parquet"), index=False)
    products.to_parquet(os.path.join(EXPORTS_DIR, "dim_products.parquet"), index=False)
    reviews.to_parquet(os.path.join(EXPORTS_DIR, "fact_order_reviews.parquet"), index=False)
    print("Core Parquet files written.")

    # 3. Pre-aggregate baseline views (Delivered orders only)
    deliv_orders = orders[orders["order_status"] == "delivered"]
    deliv_order_ids = set(deliv_orders["order_id"])
    deliv_items = items[items["order_id"].isin(deliv_order_ids)]

    # (a) Monthly trend
    merged_monthly = deliv_items.merge(deliv_orders[["order_id", "purchase_year_month"]], on="order_id")
    monthly = merged_monthly.groupby("purchase_year_month", observed=True)["price"].sum().reset_index()
    monthly.rename(columns={"purchase_year_month": "Month", "price": "Revenue"}, inplace=True)
    monthly.sort_values("Month", inplace=True)
    monthly["prev_revenue"] = monthly["Revenue"].shift(1)
    monthly["MoM_Growth_Pct"] = np.where(
        (monthly["prev_revenue"] >= 10000) & (monthly["Revenue"] >= 10000),
        ((monthly["Revenue"] - monthly["prev_revenue"]) / monthly["prev_revenue"]) * 100,
        np.nan
    )
    monthly.to_parquet(os.path.join(EXPORTS_DIR, "overview_monthly_trend.parquet"), index=False)

    # (b) State summary
    merged_cust = deliv_items.merge(deliv_orders[["order_id", "customer_id"]], on="order_id").merge(
        customers[["customer_id", "customer_state"]], on="customer_id"
    )
    tot_rev = monthly["Revenue"].sum()
    state_agg = merged_cust.groupby("customer_state", observed=True).agg(
        Revenue=("price", "sum"),
        order_count=("order_id", "nunique")
    ).reset_index().sort_values("Revenue", ascending=False)
    state_agg["share_pct"] = (state_agg["Revenue"] / tot_rev) * 100
    state_agg.to_parquet(os.path.join(EXPORTS_DIR, "overview_state_summary.parquet"), index=False)

    # (c) Category group summary
    merged_prod = deliv_items.merge(products[["product_id", "category_group", "product_category_name_english"]], on="product_id")
    cat_agg = merged_prod.groupby("category_group", observed=True).agg(
        total_revenue_brl=("price", "sum"),
        order_count=("order_id", "nunique"),
        assumed_gross_profit_brl=("assumed_gross_profit_brl", "sum"),
        units_sold=("price", "count")
    ).reset_index().sort_values("total_revenue_brl", ascending=False)
    cat_agg["blended_gross_margin_pct"] = (cat_agg["assumed_gross_profit_brl"] / cat_agg["total_revenue_brl"]) * 100
    cat_agg["share_pct"] = (cat_agg["total_revenue_brl"] / tot_rev) * 100
    cat_agg.to_parquet(os.path.join(EXPORTS_DIR, "products_category_summary.parquet"), index=False)

    # (d) Top 20 best-selling products
    top20_sku = merged_prod.groupby(["product_id", "product_category_name_english", "category_group"], observed=True).agg(
        units_sold=("price", "count"),
        total_revenue=("price", "sum"),
        assumed_gross_profit=("assumed_gross_profit_brl", "sum")
    ).reset_index().sort_values("total_revenue", ascending=False).head(20)
    top20_sku.to_parquet(os.path.join(EXPORTS_DIR, "products_top20_summary.parquet"), index=False)

    # (e) Delivery Delay daily aggregated scatter (days <= 60 and count >= 20)
    merged_rev = reviews.merge(deliv_orders[["order_id", "delivery_delay_days"]], on="order_id")
    late_rev = merged_rev[merged_rev["delivery_delay_days"] > 0]
    daily_delay = late_rev.groupby("delivery_delay_days")["review_score"].agg(["mean", "count"]).reset_index()
    daily_delay = daily_delay[(daily_delay["delivery_delay_days"] <= 60) & (daily_delay["count"] >= 20)]
    daily_delay.rename(columns={"mean": "avg_review_score", "count": "review_count"}, inplace=True)
    daily_delay.to_parquet(os.path.join(EXPORTS_DIR, "delivery_delay_daily.parquet"), index=False)

    # (f) Lead time distribution histogram (integer bins 1 to 60)
    lt_series = deliv_orders["delivery_lead_time_days"].dropna()
    lt_binned = lt_series[(lt_series >= 1) & (lt_series <= 60)].round().astype(int).value_counts().reset_index()
    lt_binned.columns = ["lead_time_days", "order_count"]
    lt_binned.sort_values("lead_time_days", inplace=True)
    lt_binned.to_parquet(os.path.join(EXPORTS_DIR, "lead_time_distribution.parquet"), index=False)

    print("All pre-aggregated Parquet files successfully generated!")

if __name__ == "__main__":
    generate_all()

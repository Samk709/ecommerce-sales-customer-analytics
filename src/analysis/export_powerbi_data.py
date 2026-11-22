"""
==============================================================================
Phase 5: Power BI Desktop Data Export Pipeline (Star Schema)
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, MySQL 8.0, Pandas

Scope:
Extracts, enriches, and exports star-schema dimension and fact tables
to data/exports/ for direct ingestion into Power BI Desktop:
1. dim_orders.csv (enriched with fulfillment SLA metrics)
2. dim_customers.csv (enriched with RFM segments and repeat customer flags)
3. dim_products.csv (enriched with macro category groups and margin rates)
4. dim_sellers.csv
5. dim_calendar.csv (standard continuous date dimension: 2016-01-01 to 2018-12-31)
6. fact_order_items.csv (enriched with assumed COGS and gross profit in BRL)
7. fact_order_payments.csv
8. fact_order_reviews.csv
==============================================================================
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.database.db_connection import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [powerbi_export]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("powerbi_export")

EXPORTS_DIR = "data/exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)

def export_calendar_dimension():
    logger.info("Generating dim_calendar.csv (2016-01-01 to 2018-12-31)...")
    date_range = pd.date_range(start="2016-01-01", end="2018-12-31", freq="D")
    
    cal = pd.DataFrame({"date_key": date_range})
    cal["Date"] = cal["date_key"].dt.strftime("%Y-%m-%d")
    cal["Year"] = cal["date_key"].dt.year
    cal["Quarter"] = cal["date_key"].dt.quarter
    cal["QuarterName"] = "Q" + cal["Quarter"].astype(str)
    cal["Month"] = cal["date_key"].dt.month
    cal["MonthName"] = cal["date_key"].dt.strftime("%B")
    cal["MonthShort"] = cal["date_key"].dt.strftime("%b")
    cal["YearMonth"] = cal["date_key"].dt.strftime("%Y-%m")
    cal["YearMonthInt"] = cal["Year"] * 100 + cal["Month"]
    cal["WeekNumber"] = cal["date_key"].dt.isocalendar().week.astype(int)
    cal["DayOfWeek"] = cal["date_key"].dt.dayofweek + 1  # 1 = Monday, 7 = Sunday
    cal["DayName"] = cal["date_key"].dt.strftime("%A")
    cal["IsWeekend"] = cal["DayOfWeek"].apply(lambda d: 1 if d in [6, 7] else 0)

    cal_path = os.path.join(EXPORTS_DIR, "dim_calendar.csv")
    cal.to_csv(cal_path, index=False)
    logger.info(f"Exported dim_calendar.csv ({len(cal):,} days) -> {cal_path}")
    return cal

def export_orders_dimension(engine):
    logger.info("Extracting and enriching dim_orders.csv...")
    query = """
    SELECT 
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date
    FROM dim_orders;
    """
    df = pd.read_sql(query, engine)
    
    # Standardize dates and timestamps
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_approved_at"] = pd.to_datetime(df["order_approved_at"])
    df["order_delivered_carrier_date"] = pd.to_datetime(df["order_delivered_carrier_date"])
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
    df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])

    # Date Keys for Power BI Active / Inactive calendar relationships
    df["order_purchase_date"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m-%d")
    df["order_delivered_customer_date_only"] = df["order_delivered_customer_date"].dt.strftime("%Y-%m-%d")
    df["order_estimated_delivery_date_only"] = df["order_estimated_delivery_date"].dt.strftime("%Y-%m-%d")

    # Delivery performance metrics (calendar-day based, matching Query 13 and Query 8)
    def calc_delay_days(row):
        if pd.isna(row["order_delivered_customer_date"]) or pd.isna(row["order_estimated_delivery_date"]):
            return np.nan
        return (row["order_delivered_customer_date"].date() - row["order_estimated_delivery_date"].date()).days

    df["delivery_delay_days"] = df.apply(calc_delay_days, axis=1)
    df["is_delayed"] = df["delivery_delay_days"].apply(lambda d: 1 if d > 0 else (0 if pd.notna(d) else np.nan))
    
    # Delivery Lead Times (purchase to delivery) in decimal days
    df["delivery_lead_time_days"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.total_seconds() / 86400.0
    # Carrier Transit Time (carrier dispatch to customer delivery) in decimal days
    df["carrier_transit_time_days"] = (df["order_delivered_customer_date"] - df["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0

    out_path = os.path.join(EXPORTS_DIR, "dim_orders.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported dim_orders.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_customers_dimension(engine):
    logger.info("Extracting and enriching dim_customers.csv with RFM intelligence...")
    query = """
    SELECT 
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    FROM dim_customers;
    """
    df = pd.read_sql(query, engine)

    # Merge with RFM Customer Segments if generated
    rfm_path = os.path.join(EXPORTS_DIR, "rfm_customer_segments.csv")
    if os.path.exists(rfm_path):
        rfm_df = pd.read_csv(rfm_path)
        rfm_sub = rfm_df[["customer_unique_id", "recency", "frequency", "monetary", "segment"]].rename(
            columns={
                "recency": "rfm_recency_days",
                "frequency": "customer_delivered_orders",
                "monetary": "customer_delivered_revenue_brl",
                "segment": "rfm_segment"
            }
        )
        df = df.merge(rfm_sub, on="customer_unique_id", how="left")
        df["rfm_segment"] = df["rfm_segment"].fillna("Inactive")
        df["customer_delivered_orders"] = df["customer_delivered_orders"].fillna(0).astype(int)
        df["customer_delivered_revenue_brl"] = df["customer_delivered_revenue_brl"].fillna(0.0)
        df["is_repeat_customer"] = df["customer_delivered_orders"].apply(lambda f: 1 if f >= 2 else 0)
    else:
        logger.warning("rfm_customer_segments.csv not found; exporting base customers.")
        df["rfm_segment"] = "Unsegmented"
        df["is_repeat_customer"] = 0

    out_path = os.path.join(EXPORTS_DIR, "dim_customers.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported dim_customers.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_products_dimension(engine):
    logger.info("Extracting dim_products.csv...")
    query = """
    SELECT 
        product_id,
        product_category_name,
        product_category_name_english,
        category_group,
        product_name_lenght AS product_name_length,
        product_description_lenght AS product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,
        assumed_cogs_rate,
        assumed_gross_margin_rate
    FROM dim_products;
    """
    df = pd.read_sql(query, engine)
    out_path = os.path.join(EXPORTS_DIR, "dim_products.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported dim_products.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_sellers_dimension(engine):
    logger.info("Extracting dim_sellers.csv...")
    query = """
    SELECT 
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    FROM dim_sellers;
    """
    df = pd.read_sql(query, engine)
    out_path = os.path.join(EXPORTS_DIR, "dim_sellers.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported dim_sellers.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_fact_order_items(engine):
    logger.info("Extracting and enriching fact_order_items.csv...")
    query = """
    SELECT 
        i.order_id,
        i.order_item_id,
        i.product_id,
        i.seller_id,
        i.shipping_limit_date,
        i.price,
        i.freight_value,
        p.assumed_cogs_rate,
        p.assumed_gross_margin_rate,
        (i.price * p.assumed_cogs_rate) AS assumed_cogs_brl,
        (i.price * p.assumed_gross_margin_rate) AS assumed_gross_profit_brl,
        ROUND(i.price + i.freight_value, 2) AS total_item_value_brl
    FROM fact_order_items i
    JOIN dim_products p ON i.product_id = p.product_id;
    """
    df = pd.read_sql(query, engine)
    out_path = os.path.join(EXPORTS_DIR, "fact_order_items.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported fact_order_items.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_fact_order_payments(engine):
    logger.info("Extracting fact_order_payments.csv...")
    query = """
    SELECT 
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    FROM fact_order_payments;
    """
    df = pd.read_sql(query, engine)
    out_path = os.path.join(EXPORTS_DIR, "fact_order_payments.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported fact_order_payments.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_fact_order_reviews(engine):
    logger.info("Extracting fact_order_reviews.csv...")
    query = """
    SELECT 
        review_id,
        order_id,
        review_score,
        review_creation_date,
        review_answer_timestamp
    FROM fact_order_reviews;
    """
    df = pd.read_sql(query, engine)
    out_path = os.path.join(EXPORTS_DIR, "fact_order_reviews.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Exported fact_order_reviews.csv ({len(df):,} rows) -> {out_path}")
    return df

def export_all():
    logger.info("Starting Power BI Star Schema Data Export Pipeline...")
    engine = get_engine(include_database=True)

    export_calendar_dimension()
    export_orders_dimension(engine)
    export_customers_dimension(engine)
    export_products_dimension(engine)
    export_sellers_dimension(engine)
    export_fact_order_items(engine)
    export_fact_order_payments(engine)
    export_fact_order_reviews(engine)

    logger.info("All Power BI Star Schema CSVs successfully exported to data/exports/!")

if __name__ == "__main__":
    export_all()

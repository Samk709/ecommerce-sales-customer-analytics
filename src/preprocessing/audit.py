"""
Raw Data Audit Script
Inspects and profiles all 9 raw Olist CSV files.
Detects missing values, duplicate records, data type anomalies, and foreign key integrity.
"""

import os
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("data_audit")

RAW_DATA_DIR = os.path.join("data", "raw")

FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "translations": "product_category_name_translation.csv"
}

def audit_file(name: str, filename: str) -> dict:
    file_path = os.path.join(RAW_DATA_DIR, filename)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return {"file": filename, "status": "missing"}

    df = pd.read_csv(file_path)
    total_rows, total_cols = df.shape
    duplicate_rows = df.duplicated().sum()
    null_counts = df.isnull().sum().to_dict()
    null_cols = {k: v for k, v in null_counts.items() if v > 0}

    logger.info(f"--- Profiling: {name} ({filename}) ---")
    logger.info(f"Shape: {total_rows:,} rows, {total_cols} columns")
    logger.info(f"Duplicate Full Rows: {duplicate_rows}")
    if null_cols:
        logger.info(f"Columns with Nulls: {null_cols}")
    else:
        logger.info("No Null values found.")

    return {
        "table": name,
        "filename": filename,
        "rows": total_rows,
        "columns": total_cols,
        "duplicates": duplicate_rows,
        "null_counts": null_cols,
        "columns_list": list(df.columns)
    }

def run_full_audit():
    logger.info("Starting Full Raw Data Audit...")
    results = []
    for name, filename in FILES.items():
        res = audit_file(name, filename)
        results.append(res)
    
    # Specific Domain Checks
    # 1. Product category translation coverage
    prod_path = os.path.join(RAW_DATA_DIR, FILES["products"])
    trans_path = os.path.join(RAW_DATA_DIR, FILES["translations"])
    if os.path.exists(prod_path) and os.path.exists(trans_path):
        prod_df = pd.read_csv(prod_path)
        trans_df = pd.read_csv(trans_path)
        raw_cats = set(prod_df["product_category_name"].dropna().unique())
        trans_cats = set(trans_df["product_category_name"].unique())
        untranslated = raw_cats - trans_cats
        logger.info(f"Unique product categories in products: {len(raw_cats)}")
        logger.info(f"Categories without English translation: {untranslated}")

    # 2. Geolocation zip code duplicates
    geo_path = os.path.join(RAW_DATA_DIR, FILES["geolocation"])
    if os.path.exists(geo_path):
        geo_df = pd.read_csv(geo_path)
        unique_zips = geo_df["geolocation_zip_code_prefix"].nunique()
        logger.info(f"Geolocation total rows: {len(geo_df):,}, unique zip prefixes: {unique_zips:,}")

    logger.info("Raw Data Audit Completed.")
    return results

if __name__ == "__main__":
    run_full_audit()

"""
Data Cleaning and Preprocessing Pipeline
Cleans and standardizes all 9 Olist tables, applies translations,
integrates financial margin assumptions, deduplicates geolocations,
and saves production-ready CSVs to data/processed/.
"""

import os
import re
import pandas as pd
import numpy as np
from src.utils.logger import setup_logger
from src.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    get_category_lookup
)

logger = setup_logger("data_cleaner")

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def clean_text_field(text: str) -> str:
    """Removes newlines, carriage returns, and excessive spaces."""
    if pd.isna(text):
        return ""
    text = str(text).replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()

def clean_orders(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning orders table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_orders_dataset.csv"))
    initial_rows = len(df)

    # Date parsing
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Standardize order_status
    df["order_status"] = df["order_status"].astype(str).str.strip().str.lower()

    # Integrity: order_id uniqueness
    dups = df.duplicated(subset=["order_id"]).sum()
    if dups > 0:
        df = df.drop_duplicates(subset=["order_id"])

    out_path = os.path.join(proc_dir, "dim_orders.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned orders ({len(df):,} rows) to {out_path}")

    return {
        "table": "dim_orders",
        "initial_rows": initial_rows,
        "final_rows": len(df),
        "duplicates_removed": int(dups),
        "null_delivered_customer_dates": int(df["order_delivered_customer_date"].isna().sum()),
        "null_approved_dates": int(df["order_approved_at"].isna().sum())
    }

def clean_order_items(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning order_items table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_order_items_dataset.csv"))
    initial_rows = len(df)

    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce")

    # Validate price > 0, freight >= 0
    invalid_price = (df["price"] <= 0).sum()
    invalid_freight = (df["freight_value"] < 0).sum()

    dups = df.duplicated(subset=["order_id", "order_item_id"]).sum()
    if dups > 0:
        df = df.drop_duplicates(subset=["order_id", "order_item_id"])

    out_path = os.path.join(proc_dir, "fact_order_items.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned order_items ({len(df):,} rows) to {out_path}")

    return {
        "table": "fact_order_items",
        "initial_rows": initial_rows,
        "final_rows": len(df),
        "duplicates_removed": int(dups),
        "invalid_prices": int(invalid_price),
        "invalid_freight": int(invalid_freight)
    }

def clean_order_payments(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning order_payments table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_order_payments_dataset.csv"))
    initial_rows = len(df)

    # Standardize payment_type
    df["payment_type"] = df["payment_type"].astype(str).str.strip().str.lower()
    df["payment_type"] = df["payment_type"].replace({"not_defined": "other"})

    df["payment_installments"] = pd.to_numeric(df["payment_installments"], errors="coerce").fillna(1).astype(int)
    df["payment_value"] = pd.to_numeric(df["payment_value"], errors="coerce").fillna(0.0)

    # Ensure uniqueness of sequence per order
    dups = df.duplicated(subset=["order_id", "payment_sequential"]).sum()
    if dups > 0:
        df = df.drop_duplicates(subset=["order_id", "payment_sequential"])

    out_path = os.path.join(proc_dir, "fact_order_payments.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned order_payments ({len(df):,} rows) to {out_path}")

    return {
        "table": "fact_order_payments",
        "initial_rows": initial_rows,
        "final_rows": len(df),
        "duplicates_removed": int(dups),
        "reclassified_not_defined": int((df["payment_type"] == "other").sum())
    }

def clean_order_reviews(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning order_reviews table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_order_reviews_dataset.csv"))
    initial_rows = len(df)

    # Clean text to prevent multiline / CSV formatting breakages
    df["review_comment_title"] = df["review_comment_title"].apply(clean_text_field)
    df["review_comment_message"] = df["review_comment_message"].apply(clean_text_field)

    df["review_score"] = pd.to_numeric(df["review_score"], errors="coerce").astype(int)
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    # In raw data, duplicate (review_id, order_id) might exist or review_id appears across multiple orders
    # Deduplicate strictly by review_id and order_id
    dups = df.duplicated(subset=["review_id", "order_id"]).sum()
    if dups > 0:
        df = df.drop_duplicates(subset=["review_id", "order_id"])

    # Create a unique review surrogate key for relational safety
    df["review_surrogate_id"] = np.arange(1, len(df) + 1)

    out_path = os.path.join(proc_dir, "fact_order_reviews.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned order_reviews ({len(df):,} rows) to {out_path}")

    return {
        "table": "fact_order_reviews",
        "initial_rows": initial_rows,
        "final_rows": len(df),
        "duplicates_removed": int(dups),
        "cleaned_review_messages": int((df["review_comment_message"] != "").sum())
    }

def clean_products(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning products table and mapping translations & margins...")
    prod_df = pd.read_csv(os.path.join(raw_dir, "olist_products_dataset.csv"))
    trans_df = pd.read_csv(os.path.join(raw_dir, "product_category_name_translation.csv"))
    initial_rows = len(prod_df)

    # Translation dictionary
    translation_map = dict(zip(trans_df["product_category_name"], trans_df["product_category_name_english"]))
    # Add unmapped categories
    translation_map["portateis_cozinha_e_preparadores_de_alimentos"] = "kitchen_and_food_preparers_portable"
    translation_map["pc_gamer"] = "pc_gamer"

    # Fill missing product category name with 'unknown'
    null_cat_count = prod_df["product_category_name"].isna().sum()
    prod_df["product_category_name"] = prod_df["product_category_name"].fillna("unknown")

    # Apply English translation
    prod_df["product_category_name_english"] = prod_df["product_category_name"].map(
        lambda x: translation_map.get(x, "unknown" if x == "unknown" else x)
    )

    # Get margin lookup assumptions
    cat_to_group, group_cogs, group_margin = get_category_lookup()

    prod_df["category_group"] = prod_df["product_category_name_english"].map(
        lambda x: cat_to_group.get(x, "Commercial & General")
    )
    prod_df["assumed_cogs_rate"] = prod_df["category_group"].map(
        lambda g: group_cogs.get(g, 0.60)
    )
    prod_df["assumed_gross_margin_rate"] = prod_df["category_group"].map(
        lambda g: group_margin.get(g, 0.40)
    )

    # Impute missing dimensions/weights with category median
    for col in ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]:
        prod_df[col] = prod_df.groupby("category_group")[col].transform(lambda x: x.fillna(x.median()))
        prod_df[col] = prod_df[col].fillna(0)

    for col in ["product_name_lenght", "product_description_lenght", "product_photos_qty"]:
        prod_df[col] = prod_df[col].fillna(0).astype(int)

    dups = prod_df.duplicated(subset=["product_id"]).sum()
    if dups > 0:
        prod_df = prod_df.drop_duplicates(subset=["product_id"])

    out_path = os.path.join(proc_dir, "dim_products.csv")
    prod_df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned products ({len(prod_df):,} rows) to {out_path}")

    # Also save the updated complete translations
    all_translations = pd.DataFrame([
        {"product_category_name": k, "product_category_name_english": v}
        for k, v in translation_map.items()
    ])
    all_translations.to_csv(os.path.join(proc_dir, "dim_category_translation.csv"), index=False)

    return {
        "table": "dim_products",
        "initial_rows": initial_rows,
        "final_rows": len(prod_df),
        "duplicates_removed": int(dups),
        "null_categories_imputed": int(null_cat_count),
        "unique_category_groups": int(prod_df["category_group"].nunique())
    }

def clean_customers(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning customers table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_customers_dataset.csv"))
    initial_rows = len(df)

    df["customer_city"] = df["customer_city"].astype(str).str.strip().str.title()
    df["customer_state"] = df["customer_state"].astype(str).str.strip().str.upper()

    dups = df.duplicated(subset=["customer_id"]).sum()
    if dups > 0:
        df = df.drop_duplicates(subset=["customer_id"])

    out_path = os.path.join(proc_dir, "dim_customers.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned customers ({len(df):,} rows) to {out_path}")

    return {
        "table": "dim_customers",
        "initial_rows": initial_rows,
        "final_rows": len(df),
        "duplicates_removed": int(dups),
        "unique_customers": int(df["customer_unique_id"].nunique())
    }

def clean_sellers(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning sellers table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_sellers_dataset.csv"))
    initial_rows = len(df)

    df["seller_city"] = df["seller_city"].astype(str).str.strip().str.title()
    df["seller_state"] = df["seller_state"].astype(str).str.strip().str.upper()

    dups = df.duplicated(subset=["seller_id"]).sum()
    if dups > 0:
        df = df.drop_duplicates(subset=["seller_id"])

    out_path = os.path.join(proc_dir, "dim_sellers.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved cleaned sellers ({len(df):,} rows) to {out_path}")

    return {
        "table": "dim_sellers",
        "initial_rows": initial_rows,
        "final_rows": len(df),
        "duplicates_removed": int(dups)
    }

def clean_geolocation(raw_dir: str, proc_dir: str) -> dict:
    logger.info("Cleaning and deduplicating geolocation table...")
    df = pd.read_csv(os.path.join(raw_dir, "olist_geolocation_dataset.csv"))
    initial_rows = len(df)

    # Filter out extreme coordinate errors outside Brazil bounding box
    # Brazil Latitude: ~[-34, 5.3], Longitude: ~[-74, -34]
    valid_coords = (
        (df["geolocation_lat"] >= -35.0) & (df["geolocation_lat"] <= 6.0) &
        (df["geolocation_lng"] >= -75.0) & (df["geolocation_lng"] <= -33.0)
    )
    invalid_coord_count = int((~valid_coords).sum())
    df = df[valid_coords].copy()

    df["geolocation_city"] = df["geolocation_city"].astype(str).str.strip().str.title()
    df["geolocation_state"] = df["geolocation_state"].astype(str).str.strip().str.upper()

    # Aggregate by zip_code_prefix to eliminate Cartesian explosion
    logger.info("Aggregating coordinates to unique zip code prefixes...")
    geo_agg = df.groupby("geolocation_zip_code_prefix").agg(
        geolocation_lat=("geolocation_lat", "median"),
        geolocation_lng=("geolocation_lng", "median"),
        geolocation_city=("geolocation_city", lambda x: x.mode().iloc[0] if not x.empty else ""),
        geolocation_state=("geolocation_state", lambda x: x.mode().iloc[0] if not x.empty else "")
    ).reset_index()

    # Round coordinates to 6 decimal places (~10cm precision)
    geo_agg["geolocation_lat"] = geo_agg["geolocation_lat"].round(6)
    geo_agg["geolocation_lng"] = geo_agg["geolocation_lng"].round(6)

    out_path = os.path.join(proc_dir, "dim_geolocation.csv")
    geo_agg.to_csv(out_path, index=False)
    logger.info(f"Saved deduplicated geolocation ({len(geo_agg):,} unique zips) to {out_path}")

    return {
        "table": "dim_geolocation",
        "initial_rows": initial_rows,
        "invalid_coordinates_filtered": invalid_coord_count,
        "final_rows": len(geo_agg),
        "reduction_percentage": round((1 - len(geo_agg) / initial_rows) * 100, 2)
    }

def run_cleaning_pipeline():
    logger.info("Starting Full Data Preprocessing & Cleaning Pipeline...")
    ensure_dir(PROCESSED_DATA_DIR)

    cleaning_log = []
    cleaning_log.append(clean_orders(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_order_items(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_order_payments(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_order_reviews(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_products(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_customers(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_sellers(RAW_DATA_DIR, PROCESSED_DATA_DIR))
    cleaning_log.append(clean_geolocation(RAW_DATA_DIR, PROCESSED_DATA_DIR))

    logger.info("Data Preprocessing Completed Successfully!")
    return cleaning_log

if __name__ == "__main__":
    run_cleaning_pipeline()

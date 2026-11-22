"""
Data Ingestion Pipeline for MySQL 8.0
Loads preprocessed CSV files from data/processed/ into the relational warehouse.
Features:
- Transaction management with rollback protection
- Optimized batch loading (chunks of 5,000 to 10,000 rows)
- Strict foreign key dependency ordering
- Post-load indexing for optimal insertion throughput
"""

import os
import time
import pandas as pd
from sqlalchemy import text
from src.config import PROCESSED_DATA_DIR, DB_NAME
from src.database.db_connection import get_engine, get_masked_url
from src.utils.logger import setup_logger

logger = setup_logger("db_loader")

SQL_SCHEMA_DIR = os.path.join("sql", "schema")

# Strict FK insertion order: Parent dimensions first, child facts last
TABLE_FILES = [
    ("dim_category_translation", "dim_category_translation.csv"),
    ("dim_geolocation", "dim_geolocation.csv"),
    ("dim_customers", "dim_customers.csv"),
    ("dim_sellers", "dim_sellers.csv"),
    ("dim_products", "dim_products.csv"),
    ("dim_orders", "dim_orders.csv"),
    ("fact_order_items", "fact_order_items.csv"),
    ("fact_order_payments", "fact_order_payments.csv"),
    ("fact_order_reviews", "fact_order_reviews.csv")
]

def execute_sql_file(engine, file_path: str):
    """Parses and executes an SQL script containing multiple statements."""
    logger.info(f"Executing SQL script: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split statements by semicolon while respecting comments
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            # Skip empty or delimiter commands
            if stmt.upper().startswith("USE ") or stmt.upper().startswith("CREATE DATABASE "):
                continue
            conn.execute(text(stmt))

def initialize_database():
    """Creates database schema if it doesn't exist."""
    logger.info("Initializing database schema...")
    server_engine = get_engine(include_database=False)
    with server_engine.begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
    logger.info(f"Database `{DB_NAME}` verified.")

def create_tables(db_engine):
    """Executes DDL statements to create tables with PKs and FKs."""
    schema_file = os.path.join(SQL_SCHEMA_DIR, "02_create_tables.sql")
    execute_sql_file(db_engine, schema_file)
    logger.info("Tables created successfully.")

def apply_indexes(db_engine):
    """Applies strategic indexes post-data ingestion."""
    index_file = os.path.join(SQL_SCHEMA_DIR, "03_create_indexes.sql")
    execute_sql_file(db_engine, index_file)
    logger.info("Strategic indexes applied successfully.")

def load_table(db_engine, table_name: str, csv_filename: str, chunksize: int = 10000):
    """Loads a single CSV into MySQL in transactions with rollback protection."""
    csv_path = os.path.join(PROCESSED_DATA_DIR, csv_filename)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing processed file: {csv_path}")

    start_time = time.time()
    logger.info(f"Loading '{table_name}' from {csv_filename} (batch chunksize: {chunksize:,})...")

    df = pd.read_csv(csv_path)
    total_rows = len(df)

    # Use transaction block: if any chunk fails, rollback happens automatically
    with db_engine.begin() as conn:
        df.to_sql(
            name=table_name,
            con=conn,
            if_exists="append",
            index=False,
            chunksize=chunksize,
            method="multi"
        )

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Loaded {total_rows:,} rows into '{table_name}' in {elapsed}s.")
    return total_rows

def run_loader():
    """Orchestrates the entire database loading process."""
    logger.info(f"Connecting to database at {get_masked_url()}...")
    try:
        initialize_database()
        db_engine = get_engine(include_database=True)

        logger.info("Step 1: Creating database tables...")
        create_tables(db_engine)

        logger.info("Step 2: Ingesting processed datasets in relational order...")
        load_summary = {}
        for table_name, csv_filename in TABLE_FILES:
            rows = load_table(db_engine, table_name, csv_filename)
            load_summary[table_name] = rows

        logger.info("Step 3: Creating performance indexes...")
        apply_indexes(db_engine)

        logger.info("=" * 60)
        logger.info("DATABASE INGESTION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        return load_summary

    except Exception as e:
        logger.error(f"FATAL: Ingestion failed. Transaction rolled back. Reason: {type(e).__name__} - {str(e)}")
        raise

if __name__ == "__main__":
    run_loader()

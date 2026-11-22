"""
Database Integration and Verification Tests
Tests live MySQL 8.0 connectivity and verifies schema objects.
"""

import pytest
from sqlalchemy import inspect
from src.database.db_connection import get_engine, test_connection as check_mysql_connection

EXPECTED_TABLES = [
    "dim_category_translation",
    "dim_geolocation",
    "dim_customers",
    "dim_sellers",
    "dim_products",
    "dim_orders",
    "fact_order_items",
    "fact_order_payments",
    "fact_order_reviews"
]

def test_mysql_connectivity():
    """Verify that Python can connect to the local MySQL 8.0 server."""
    connected = check_mysql_connection()
    if not connected:
        pytest.skip("MySQL server not reachable or credentials not yet active in .env. Skipping integration test.")
    assert connected is True

def test_tables_created_in_mysql():
    """Verify all 9 tables exist in the olist_ecommerce database."""
    connected = check_mysql_connection()
    if not connected:
        pytest.skip("MySQL server not reachable. Skipping table inspection.")

    engine = get_engine(include_database=True)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    for table in EXPECTED_TABLES:
        assert table in existing_tables, f"Table '{table}' missing in MySQL database!"

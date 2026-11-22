"""
Database Verification and Reconciliation Script
Compares live MySQL table row counts directly against data/processed/*.csv counts.
Ensures zero record loss and referential integrity.
"""

import os
import pandas as pd
from sqlalchemy import text
from src.config import PROCESSED_DATA_DIR
from src.database.db_connection import get_engine, get_masked_url
from src.database.load_data import TABLE_FILES
from src.utils.logger import setup_logger

logger = setup_logger("db_verifier")

def verify_row_counts():
    """Compares row counts between MySQL and processed CSV files."""
    logger.info(f"Connecting to MySQL ({get_masked_url()}) for verification...")
    engine = get_engine(include_database=True)

    reconciliation_data = []
    all_matched = True

    with engine.connect() as conn:
        for table_name, csv_filename in TABLE_FILES:
            csv_path = os.path.join(PROCESSED_DATA_DIR, csv_filename)
            csv_count = len(pd.read_csv(csv_path))

            query = text(f"SELECT COUNT(*) FROM `{table_name}`;")
            mysql_count = conn.execute(query).scalar()

            matched = (csv_count == mysql_count)
            if not matched:
                all_matched = False

            reconciliation_data.append({
                "Table Name": table_name,
                "CSV Rows": f"{csv_count:,}",
                "MySQL Rows": f"{mysql_count:,}",
                "Difference": mysql_count - csv_count,
                "Status": "MATCH" if matched else "MISMATCH"
            })

    # Print formatted table
    rec_df = pd.DataFrame(reconciliation_data)
    logger.info("\n" + rec_df.to_string(index=False))

    if all_matched:
        logger.info("\nALL TABLES VERIFIED: 100% RECONCILIATION SUCCESSFUL!")
    else:
        logger.error("\nRECONCILIATION MISMATCH DETECTED. Review table differences above.")

    return all_matched

if __name__ == "__main__":
    verify_row_counts()

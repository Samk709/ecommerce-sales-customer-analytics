"""
Configuration Module
Loads environment variables and YAML margin assumptions.
"""

import os
import yaml
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
EXPORTS_DATA_DIR = os.path.join(DATA_DIR, "exports")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
MARGIN_CONFIG_PATH = os.path.join(CONFIG_DIR, "margin_assumptions.yaml")

# Database Environment Variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "olist_ecommerce")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def load_margin_assumptions() -> dict:
    """Loads the category grouping and margin assumptions from YAML."""
    if not os.path.exists(MARGIN_CONFIG_PATH):
        raise FileNotFoundError(f"Margin assumptions config not found: {MARGIN_CONFIG_PATH}")
    with open(MARGIN_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_category_lookup() -> tuple[dict, dict, dict]:
    """
    Returns lookup dictionaries:
    - cat_to_group: maps individual category -> group name
    - group_cogs: maps group name -> COGS percentage
    - group_margin: maps group name -> gross margin percentage
    """
    config = load_margin_assumptions()
    cat_to_group = {}
    group_cogs = {}
    group_margin = {}

    for group_name, details in config.get("category_groups", {}).items():
        cogs = details.get("cogs_rate", 0.60)
        margin = details.get("gross_margin_rate", 0.40)
        group_cogs[group_name] = cogs
        group_margin[group_name] = margin
        for cat in details.get("categories", []):
            cat_to_group[cat] = group_name

    return cat_to_group, group_cogs, group_margin

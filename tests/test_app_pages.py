"""
Phase 7 Smoke Tests: Streamlit App Page Rendering Verification
Uses streamlit.testing.v1.AppTest to ensure all 5 dashboard views and tabs
render cleanly with zero exceptions from the repository exports alone.
"""

import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "streamlit_app" / "app.py")

PAGE_MAPPING = {
    "overview": "🏠 Executive Overview",
    "products": "📦 Products & Categories",
    "customers": "👥 Customers & Retention",
    "delivery": "🚚 Logistics SLA & CSAT",
    "forecast": "📈 Sales Forecast"
}

def test_page_overview_renders():
    """Verify Executive Overview page loads, runs without exception, and displays verified financial KPIs."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert len(at.exception) == 0, f"Overview encountered exceptions: {at.exception}"
    
    # Verify rendered card values and tooltips
    rendered_text = " ".join([m.value for m in at.markdown])
    assert "Total Checkout GMV: R$ 15,419,773.75" in rendered_text
    assert "Assumed Gross Profit: R$ 5,388,818.98" in rendered_text
    assert "Freight: R$ 2,198,276" in rendered_text
    assert "40.8% assumed margin" in rendered_text
    assert "R$ 13,221,498.11 net" in rendered_text

def test_page_products_renders():
    """Verify Products & Categories page loads without KeyError or exceptions."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    r = at.sidebar.radio[0]
    r.set_value(PAGE_MAPPING["products"]).run()
    assert len(at.exception) == 0, f"Products page encountered exceptions: {at.exception}"

def test_page_customers_renders():
    """Verify Customers & Retention page loads without KeyError or exceptions."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    r = at.sidebar.radio[0]
    r.set_value(PAGE_MAPPING["customers"]).run()
    assert len(at.exception) == 0, f"Customers page encountered exceptions: {at.exception}"

def test_page_delivery_renders():
    """Verify Delivery SLA & CSAT page loads without KeyError or exceptions."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    r = at.sidebar.radio[0]
    r.set_value(PAGE_MAPPING["delivery"]).run()
    assert len(at.exception) == 0, f"Delivery page encountered exceptions: {at.exception}"

def test_page_forecast_renders():
    """Verify Sales Forecast page loads without KeyError or exceptions."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    r = at.sidebar.radio[0]
    r.set_value(PAGE_MAPPING["forecast"]).run()
    assert len(at.exception) == 0, f"Forecast page encountered exceptions: {at.exception}"

def test_filtered_view_renders():
    """Verify dashboard renders cleanly with state filter applied (e.g. SP)."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    # Filter state multiselect
    state_ms = at.sidebar.multiselect[1]  # second multiselect is State
    state_ms.set_value(["SP"]).run()
    assert len(at.exception) == 0, f"Filtered view encountered exceptions: {at.exception}"

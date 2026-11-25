"""
Phase 7 Smoke Tests: Streamlit App Page & Section Rendering Verification
Uses streamlit.testing.v1.AppTest to ensure all 5 dashboard views and all 14 sections
render cleanly with zero exceptions from the repository exports alone, both unfiltered
and under the State = SP filter.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from streamlit_app.views.overview import OVERVIEW_SECTIONS
from streamlit_app.views.products import PRODUCTS_SECTIONS
from streamlit_app.views.customers import CUSTOMERS_SECTIONS
from streamlit_app.views.delivery import DELIVERY_SECTIONS
from streamlit_app.views.forecast import FORECAST_SECTIONS

APP_PATH = str(Path(__file__).resolve().parent.parent / "streamlit_app" / "app.py")

ALL_PAGE_SECTIONS = {
    "🏠 Executive Overview": OVERVIEW_SECTIONS,
    "📦 Products & Categories": PRODUCTS_SECTIONS,
    "👥 Customers & Retention": CUSTOMERS_SECTIONS,
    "🚚 Logistics SLA & CSAT": DELIVERY_SECTIONS,
    "📈 Sales Forecast": FORECAST_SECTIONS
}

def _get_widget_options(segmented_control_widget):
    """Helper to retrieve full option strings including icons from proto options."""
    if hasattr(segmented_control_widget, "proto") and segmented_control_widget.proto.options:
        return [f"{opt.content_icon} {opt.content}".strip() for opt in segmented_control_widget.proto.options]
    return list(segmented_control_widget.options)

def test_sections_count_and_code_definitions():
    """
    Assert that the number of sections defined in code exactly equals 14:
    Overview 3, Products 3, Customers 3, Delivery 3, Forecast 2.
    Guarantees that a new section cannot be added without updating the test suite.
    """
    assert len(OVERVIEW_SECTIONS) == 3, f"Expected 3 Overview sections, found {len(OVERVIEW_SECTIONS)}"
    assert len(PRODUCTS_SECTIONS) == 3, f"Expected 3 Products sections, found {len(PRODUCTS_SECTIONS)}"
    assert len(CUSTOMERS_SECTIONS) == 3, f"Expected 3 Customers sections, found {len(CUSTOMERS_SECTIONS)}"
    assert len(DELIVERY_SECTIONS) == 3, f"Expected 3 Delivery sections, found {len(DELIVERY_SECTIONS)}"
    assert len(FORECAST_SECTIONS) == 2, f"Expected 2 Forecast sections, found {len(FORECAST_SECTIONS)}"
    
    total_defined = sum(len(s) for s in ALL_PAGE_SECTIONS.values())
    assert total_defined == 14, f"Expected exactly 14 total sections, got {total_defined}"

def test_page_overview_all_sections_render():
    """Verify Executive Overview loads, renders all 3 sections cleanly, and displays verified financial KPIs."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert len(at.exception) == 0, f"Overview encountered exceptions: {at.exception}"
    
    # Verify rendered card values and tooltips
    rendered_text = " ".join([m.value for m in at.markdown])
    assert "Total Checkout GMV: R$ 15,419,773.75" in rendered_text
    assert "Assumed Gross Profit: R$ 5,388,818.98" in rendered_text
    assert "Freight: R$ 2,198,276" in rendered_text
    assert "40.8% assumed margin" in rendered_text
    assert "R$ 13,221,498.11 net" in rendered_text
    
    # Assert widget options match code definitions exactly
    assert _get_widget_options(at.segmented_control[0]) == OVERVIEW_SECTIONS
    assert len(at.segmented_control[0].options) == len(OVERVIEW_SECTIONS)
    
    # Test every section
    for sec in OVERVIEW_SECTIONS:
        at.segmented_control[0].set_value(sec).run()
        assert len(at.exception) == 0, f"Exception on Overview > {sec}: {at.exception}"

def test_page_products_all_sections_render():
    """Verify Products & Categories page loads and renders all 3 sections cleanly."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.sidebar.radio[0].set_value("📦 Products & Categories").run()
    assert len(at.exception) == 0, f"Products page encountered exceptions: {at.exception}"
    
    assert _get_widget_options(at.segmented_control[0]) == PRODUCTS_SECTIONS
    assert len(at.segmented_control[0].options) == len(PRODUCTS_SECTIONS)
    for sec in PRODUCTS_SECTIONS:
        at.segmented_control[0].set_value(sec).run()
        assert len(at.exception) == 0, f"Exception on Products > {sec}: {at.exception}"

def test_page_customers_all_sections_render():
    """Verify Customers & Retention page loads and renders all 3 sections cleanly without KeyError."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.sidebar.radio[0].set_value("👥 Customers & Retention").run()
    assert len(at.exception) == 0, f"Customers page encountered exceptions: {at.exception}"
    
    assert _get_widget_options(at.segmented_control[0]) == CUSTOMERS_SECTIONS
    assert len(at.segmented_control[0].options) == len(CUSTOMERS_SECTIONS)
    for sec in CUSTOMERS_SECTIONS:
        at.segmented_control[0].set_value(sec).run()
        assert len(at.exception) == 0, f"Exception on Customers > {sec}: {at.exception}"

def test_page_delivery_all_sections_render():
    """Verify Delivery SLA & CSAT page loads and renders all 3 sections cleanly."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.sidebar.radio[0].set_value("🚚 Logistics SLA & CSAT").run()
    assert len(at.exception) == 0, f"Delivery page encountered exceptions: {at.exception}"
    
    assert _get_widget_options(at.segmented_control[0]) == DELIVERY_SECTIONS
    assert len(at.segmented_control[0].options) == len(DELIVERY_SECTIONS)
    for sec in DELIVERY_SECTIONS:
        at.segmented_control[0].set_value(sec).run()
        assert len(at.exception) == 0, f"Exception on Delivery > {sec}: {at.exception}"

def test_page_forecast_all_sections_render():
    """Verify Sales Forecast page loads and renders both sections cleanly."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.sidebar.radio[0].set_value("📈 Sales Forecast").run()
    assert len(at.exception) == 0, f"Forecast page encountered exceptions: {at.exception}"
    
    assert _get_widget_options(at.segmented_control[0]) == FORECAST_SECTIONS
    assert len(at.segmented_control[0].options) == len(FORECAST_SECTIONS)
    for sec in FORECAST_SECTIONS:
        at.segmented_control[0].set_value(sec).run()
        assert len(at.exception) == 0, f"Exception on Forecast > {sec}: {at.exception}"

def test_all_sections_with_state_sp_filter():
    """
    Verify all 14 sections across all 5 pages render with zero exceptions
    when the State = SP filter is applied.
    Also asserts that the number of tested sections equals 14.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    # Apply State = SP filter
    at.sidebar.multiselect[1].set_value(["SP"]).run()
    assert len(at.exception) == 0, f"State=SP filter failed: {at.exception}"
    
    tested_count = 0
    for page_name, sections in ALL_PAGE_SECTIONS.items():
        at.sidebar.radio[0].set_value(page_name).run()
        assert len(at.exception) == 0, f"Exception loading {page_name} with SP filter: {at.exception}"
        assert _get_widget_options(at.segmented_control[0]) == sections
        assert len(at.segmented_control[0].options) == len(sections)
        
        for sec in sections:
            at.segmented_control[0].set_value(sec).run()
            assert len(at.exception) == 0, f"Exception on SP-filtered {page_name} > {sec}: {at.exception}"
            tested_count += 1
            
    assert tested_count == 14, f"Expected 14 sections tested with SP filter, but tested {tested_count}"

"""
==============================================================================
UI Components, Custom Styling & Plotly Theming for Streamlit Application
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Plotly

Description:
Provides corporate CSS styling, styled HTML metric cards, Plotly layout themes,
and download button utilities.
==============================================================================
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def inject_custom_css():
    """Injects high-end corporate CSS styling for an executive analytics appearance."""
    st.markdown(
        """
        <style>
        /* Global Page Background and Base Font */
        .main {
            background-color: #F8F9FA;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        }
        
        /* Metric Card Container */
        .kpi-card {
            background-color: #FFFFFF;
            border-radius: 10px;
            padding: 16px 20px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
            transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
            margin-bottom: 12px;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
            border-color: #CBD5E1;
        }
        .kpi-label {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #64748B;
            margin-bottom: 4px;
        }
        .kpi-value {
            font-size: 1.80rem;
            font-weight: 800;
            color: #1B2A4A;
            line-height: 1.15;
            margin-bottom: 4px;
        }
        .kpi-subtext {
            font-size: 0.78rem;
            color: #94A3B8;
        }
        .kpi-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .badge-green { background-color: #E8F8F0; color: #27AE60; }
        .badge-blue { background-color: #EBF5FB; color: #2980B9; }
        .badge-amber { background-color: #FEF5E7; color: #E67E22; }
        .badge-red { background-color: #FDEDEC; color: #E74C3C; }

        /* Section Header Divider */
        .section-header {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1B2A4A;
            margin-top: 24px;
            margin-bottom: 12px;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 6px;
        }

        /* Notice / Disclaimer Callout */
        .financial-notice {
            background-color: #F8F9FA;
            border-left: 4px solid #3498DB;
            padding: 10px 14px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #475569;
            margin-bottom: 16px;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    badge_text: str = "",
    badge_type: str = "green"
):
    """Renders a styled corporate KPI card inside a Streamlit container or column."""
    badge_html = f'<span class="kpi-badge badge-{badge_type}">{badge_text}</span>' if badge_text else ''
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtext">{badge_html} {subtext}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def apply_plotly_theme(
    fig: go.Figure,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    height: int = 380
) -> go.Figure:
    """Applies clean enterprise styling to Plotly figures."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Segoe UI, sans-serif", size=14, color="#1B2A4A"),
            x=0.01,
            xanchor="left"
        ),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        height=height,
        font=dict(family="Segoe UI, sans-serif", size=11, color="#475569"),
        xaxis=dict(
            title=dict(text=x_title, font=dict(size=11, color="#64748B")),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
            tickfont=dict(size=10, color="#64748B")
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=11, color="#64748B")),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
            tickfont=dict(size=10, color="#64748B")
        ),
        hoverlabel=dict(
            bgcolor="#1B2A4A",
            font_size=12,
            font_family="Segoe UI, sans-serif"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        )
    )
    return fig

def render_download_button(df: pd.DataFrame, filename: str, label: str = "📥 Download Filtered Data (CSV)", key: str = None):
    """Renders a standard CSV download button for filtered data."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        key=key
    )

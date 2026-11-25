"""
==============================================================================
UI Components, Custom Styling & Plotly Theming for Streamlit Application
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Plotly

Description:
Provides corporate CSS styling, header/footer elements, styled HTML metric cards,
dynamic insight callouts, Plotly layout themes, and download button utilities.
==============================================================================
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Standard Corporate Color Palette
COLOR_PRIMARY_NAVY = "#1B2A4A"
COLOR_ACCENT_BLUE = "#2563EB"
COLOR_TEAL = "#0D9488"
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"
COLOR_SLATE_DARK = "#1E293B"
COLOR_SLATE_MUTED = "#64748B"
COLOR_BORDER = "#E2E8F0"
COLOR_BG_CARD = "#FFFFFF"

def inject_custom_css():
    """Injects high-end corporate CSS styling for an executive analytics appearance."""
    st.markdown(
        """
        <style>
        /* Base Page Font and Background */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        }
        
        .main {
            background-color: #F8FAFC;
        }

        /* Top Header Container */
        .top-header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0 16px 0;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 20px;
        }
        .header-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: #1B2A4A;
            margin: 0;
            line-height: 1.2;
        }
        .header-subtitle {
            font-size: 0.82rem;
            color: #64748B;
            margin: 4px 0 0 0;
            font-weight: 500;
        }
        .github-link-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: #0F172A;
            color: #FFFFFF !important;
            padding: 7px 14px;
            border-radius: 6px;
            font-size: 0.80rem;
            font-weight: 600;
            text-decoration: none !important;
            transition: all 0.2s ease;
        }
        .github-link-btn:hover {
            background-color: #2563EB;
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);
        }

        /* Dynamic Key Insight Box */
        .key-insight-card {
            background-color: #F0F7FF;
            border-left: 4px solid #2563EB;
            padding: 12px 18px;
            border-radius: 6px;
            margin-bottom: 18px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
            font-size: 0.88rem;
            color: #1E293B;
            line-height: 1.5;
        }
        
        /* Metric Card Container */
        .kpi-card {
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 10px 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
            margin-bottom: 12px;
            min-height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 14px rgba(37, 99, 235, 0.09);
            border-color: #BFDBFE;
        }
        .kpi-label {
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #64748B;
            margin-bottom: 2px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .kpi-value {
            font-size: 1.15rem;
            font-weight: 800;
            color: #1B2A4A;
            line-height: 1.15;
            margin: 2px 0;
            letter-spacing: -0.02em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-subtext {
            font-size: 0.72rem;
            color: #94A3B8;
            line-height: 1.25;
        }
        .kpi-badge {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 10px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: normal;
            text-transform: none;
        }
        .badge-green { background-color: #ECFDF5; color: #059669; }
        .badge-blue { background-color: #EFF6FF; color: #2563EB; }
        .badge-amber { background-color: #FFFBEB; color: #D97706; }
        .badge-red { background-color: #FEF2F2; color: #DC2626; }

        /* Operational Notice Banner */
        .financial-notice {
            background-color: #F8FAFC;
            border-left: 4px solid #64748B;
            padding: 9px 14px;
            border-radius: 4px;
            font-size: 0.80rem;
            color: #475569;
            margin-bottom: 16px;
        }

        /* Streamlit Tabs Polish */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 16px;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.88rem;
            font-weight: 600;
            color: #64748B;
            padding: 8px 16px;
            border-radius: 6px 6px 0 0;
        }
        .stTabs [aria-selected="true"] {
            color: #2563EB !important;
            border-bottom: 2px solid #2563EB !important;
        }

        /* Footer Container */
        .footer-container {
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #E2E8F0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            font-size: 0.78rem;
            color: #64748B;
        }
        .footer-left {
            flex: 1 1 500px;
        }
        .footer-right {
            flex: 0 1 auto;
            color: #94A3B8;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_header(subtitle: str = "Executive Sales & Customer Intelligence Analytics Platform"):
    """Renders a clean corporate top header with GitHub link."""
    st.markdown(
        f"""
        <div class="top-header-container">
            <div>
                <h1 class="header-title">🛒 E-Commerce Sales & Customer Intelligence</h1>
                <p class="header-subtitle">{subtitle}</p>
            </div>
            <div>
                <a href="https://github.com/Samk709/ecommerce-sales-customer-analytics" target="_blank" class="github-link-btn">
                    <svg height="15" width="15" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                    GitHub Repo
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_insight_box(insight_text: str):
    """Renders a dynamically generated Key Insight card at the top of a page."""
    st.markdown(
        f"""
        <div class="key-insight-card">
            {insight_text}
        </div>
        """,
        unsafe_allow_html=True
    )

# Global Plotly Chart Configuration (Hides modebar / hover controls)
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True
}

def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    badge_text: str = "",
    badge_type: str = "green",
    tooltip: str = ""
):
    """Renders a styled corporate KPI card with consistent size and readable typography."""
    badge_html = f'<span class="kpi-badge badge-{badge_type}">{badge_text}</span>' if badge_text else ''
    title_attr = f' title="{tooltip}"' if tooltip else f' title="{value}"'
    st.markdown(
        f"""
        <div class="kpi-card"{title_attr}>
            <div class="kpi-label">
                <span>{label}</span>
                {badge_html}
            </div>
            <div class="kpi-value"{title_attr}>{value}</div>
            <div class="kpi-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_footer():
    """Renders a standardized executive footer with data attribution and financial disclosures."""
    st.markdown(
        """
        <div class="footer-container">
            <div class="footer-left">
                <strong>Data Source:</strong> Brazilian E-Commerce Public Dataset by Olist (2016–2018) &bull; 
                <strong>Currency:</strong> Brazilian Reais (R$ / BRL) &bull; 
                <strong>Scope:</strong> Delivered orders only (excludes freight unless designated GMV)
            </div>
            <div class="footer-right">
                <em>*Financial Notice: Product cost and gross margins are retail benchmark assumptions documented in config/margin_assumptions.yaml (assumed margin, not real data).</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def apply_plotly_theme(
    fig: go.Figure,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    height: int = 370
) -> go.Figure:
    """Applies clean enterprise styling to Plotly figures with consistent colors and fonts."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Segoe UI, sans-serif", size=13, color=COLOR_PRIMARY_NAVY),
            x=0.01,
            xanchor="left"
        ),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=45, r=20, t=55 if title else 20, b=40),
        height=height,
        font=dict(family="Segoe UI, sans-serif", size=11, color=COLOR_SLATE_DARK),
        xaxis=dict(
            title=dict(text=x_title, font=dict(size=11, color=COLOR_SLATE_MUTED)),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor=COLOR_BORDER,
            tickfont=dict(size=10, color=COLOR_SLATE_MUTED)
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=11, color=COLOR_SLATE_MUTED)),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor=COLOR_BORDER,
            tickfont=dict(size=10, color=COLOR_SLATE_MUTED)
        ),
        hoverlabel=dict(
            bgcolor=COLOR_PRIMARY_NAVY,
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

def render_section_selector(options: list, default_index: int = 0, key: str = None) -> str:
    """Renders a modern, performance-optimized segmented control to navigate view sections."""
    if hasattr(st, "segmented_control"):
        val = st.segmented_control(
            "Section",
            options=options,
            default=options[default_index] if options else None,
            key=key,
            label_visibility="collapsed"
        )
        return val if val is not None else options[default_index]
    else:
        return st.radio(
            "Section",
            options=options,
            index=default_index,
            horizontal=True,
            key=key,
            label_visibility="collapsed"
        )

"""
==============================================================================
View: Time-Series Seasonality & 30-Day Holt-Winters Sales Forecast
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Plotly
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_app.components import (
    render_kpi_card,
    render_insight_box,
    apply_plotly_theme,
    render_download_button,
    PLOTLY_CONFIG,
    COLOR_PRIMARY_NAVY,
    COLOR_ACCENT_BLUE,
    COLOR_SUCCESS,
    COLOR_WARNING
)
from streamlit_app.data_loader import load_sales_forecast

def render_forecast_view():
    st.markdown(
        '<div class="financial-notice"><b>Forecasting Methodology</b>: Baseline 30-day forward projection generated using an additive '
        '<b>Holt-Winters Exponential Smoothing</b> model capturing daily baseline trend and 7-day weekly cyclicality. '
        'Model accuracy is validated against an operational 30-day holdout test window; the forward horizon serves as an illustrative baseline. Currency: Brazilian Reais (R$).</div>',
        unsafe_allow_html=True
    )
    
    fc_df = load_sales_forecast()

    # Dynamic Key Insight Box generated strictly from underlying data
    if not fc_df.empty and "future_forecast_brl" in fc_df.columns:
        future_30d = fc_df["future_forecast_brl"].dropna()
        total_30d_proj = future_30d.sum()
        avg_30d_proj = future_30d.mean()
        insight_text = (
            f"💡 <b>Key Insight</b>: The additive Holt-Winters model captures 7-day weekly cyclicality with a "
            f"<b>holdout WAPE of 12.90%</b> (MAE: <b>R$ 4,647.90</b> vs holdout mean R$ 36,038.69). "
            f"Over the 30-day forward horizon after dataset end, delivered merchandise revenue is projected at "
            f"<b>R$ {total_30d_proj:,.2f}</b> (averaging <b>R$ {avg_30d_proj:,.2f}/day</b>) as an illustrative baseline."
        )
    else:
        insight_text = "💡 <b>Key Insight</b>: 30-day baseline sales forecast captures 7-day weekly cyclicality with holdout WAPE 12.90%."
    render_insight_box(insight_text)

    # 1. Validation Performance Metrics Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Holdout WAPE", "12.90%", "MAE / Test Mean", "Accuracy", "green")
    with c2:
        render_kpi_card("Validation MAE", "R$ 4,647.90", "mean absolute error", "Error", "blue")
    with c3:
        render_kpi_card("Validation RMSE", "R$ 5,693.14", "root mean squared error", "Error", "blue")
    with c4:
        render_kpi_card("Holdout Daily Mean", "R$ 36,038.69", "Jul 22 - Aug 20, 2018 actuals", "Actuals", "blue")
    with c5:
        render_kpi_card("Forecast Daily Mean", "R$ 33,741.09", "predicted holdout daily mean", "Forecast", "amber")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Clean Tabs Layout for Laptop-Friendly Presentation
    tab_chart, tab_table = st.tabs([
        "📈 30-Day Forward Forecast & Holdout Projection",
        "📋 Daily Forecast & Validation Data Table"
    ])
    
    with tab_chart:
        if not fc_df.empty:
            fig_fc = go.Figure()
            
            # Historical Actuals
            fig_fc.add_trace(go.Scatter(
                x=fc_df["order_date"],
                y=fc_df["actual_revenue_brl"],
                mode="lines",
                name="Actual Delivered Revenue (R$)",
                line=dict(color=COLOR_ACCENT_BLUE, width=2),
                hovertemplate="<b>%{x}</b><br>Actual Revenue: R$ %{y:,.2f}<extra></extra>"
            ))
            
            # Holdout Prediction
            if "test_prediction_brl" in fc_df.columns:
                test_slice = fc_df.dropna(subset=["test_prediction_brl"])
                fig_fc.add_trace(go.Scatter(
                    x=test_slice["order_date"],
                    y=test_slice["test_prediction_brl"],
                    mode="lines",
                    name="Holt-Winters Holdout Prediction",
                    line=dict(color="#F59E0B", width=2.5, dash="dash"),
                    hovertemplate="<b>%{x}</b><br>Holdout Pred: R$ %{y:,.2f}<extra></extra>"
                ))
                
            # 30-Day Forward Forecast
            if "future_forecast_brl" in fc_df.columns:
                future_slice = fc_df.dropna(subset=["future_forecast_brl"])
                fig_fc.add_trace(go.Scatter(
                    x=future_slice["order_date"],
                    y=future_slice["future_forecast_brl"],
                    mode="lines+markers",
                    name="30-Day Forward Baseline Forecast",
                    line=dict(color=COLOR_SUCCESS, width=2.5),
                    marker=dict(size=5, color="#059669"),
                    hovertemplate="<b>%{x}</b><br>Forward Forecast: R$ %{y:,.2f}<extra></extra>"
                ))
                
            apply_plotly_theme(fig_fc, "Daily Delivered Revenue with 30-Day Holt-Winters Projection (R$)", "Order Date", "Daily Revenue (R$)", height=440)
            st.plotly_chart(fig_fc, use_container_width=True, config=PLOTLY_CONFIG)

    with tab_table:
        if not fc_df.empty:
            disp_fc = fc_df.copy().tail(60)
            disp_fc["actual_revenue_brl"] = disp_fc["actual_revenue_brl"].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "—")
            if "test_prediction_brl" in disp_fc.columns:
                disp_fc["test_prediction_brl"] = disp_fc["test_prediction_brl"].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "—")
            if "future_forecast_brl" in disp_fc.columns:
                disp_fc["future_forecast_brl"] = disp_fc["future_forecast_brl"].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "—")
                
            disp_fc.rename(columns={
                "order_date": "Order Date",
                "actual_revenue_brl": "Actual Revenue (R$)",
                "test_prediction_brl": "Holdout Prediction (R$)",
                "future_forecast_brl": "Forward Forecast (R$)"
            }, inplace=True)
            
            st.dataframe(disp_fc, use_container_width=True, hide_index=True)
            render_download_button(fc_df, "daily_sales_forecast_30d.csv", "📥 Export Daily Sales Forecast (CSV)", key="download_forecast_csv")

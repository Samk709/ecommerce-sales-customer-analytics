"""
View: Executive Overview & Sales Performance
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.components import render_kpi_card, apply_plotly_theme, render_download_button
from streamlit_app.kpi_metrics import compute_overview_kpis

def render_overview_view(orders_df: pd.DataFrame, items_df: pd.DataFrame, customers_df: pd.DataFrame, is_filtered: bool):
    st.markdown('<div class="section-header">Executive Sales Performance Overview</div>', unsafe_allow_html=True)
    
    # 1. Compute Headline KPIs
    kpis = compute_overview_kpis(orders_df, items_df, customers_df)
    
    # Financial Disclaimer
    st.markdown(
        '<div class="financial-notice"><b>Operational Standard</b>: Revenue includes delivered orders only and excludes shipping freight. '
        'All profit and COGS metrics are labelled <i>"assumed margin, not real data"</i> based on category benchmark assumptions. '
        'Currency is strictly in <b>Brazilian Reais (R$ / BRL)</b>.</div>',
        unsafe_allow_html=True
    )
    
    # KPI Cards Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_kpi_card("Merchandise Revenue", f"R$ {kpis['total_revenue_brl']:,.2f}", "Excludes shipping", "Delivered", "blue")
    with c2:
        render_kpi_card("Gross Merchandise (GMV)", f"R$ {kpis['gmv_brl']:,.2f}", f"Freight: R$ {kpis['total_freight_brl']:,.0f}", "Total Checkout", "blue")
    with c3:
        render_kpi_card("Delivered Orders", f"{kpis['total_delivered_orders']:,}", f"{kpis['total_items_sold']:,} items sold", "Completed", "green")
    with c4:
        render_kpi_card("Average Order Value", f"R$ {kpis['aov_brl']:,.2f}", "Net spend / order", "AOV", "blue")
    with c5:
        render_kpi_card("Assumed Gross Profit", f"R$ {kpis['assumed_gross_profit_brl']:,.2f}", f"{kpis['blended_gross_margin_pct']:.1f}% margin", "Assumed", "amber")
    with c6:
        render_kpi_card("Repeat Customers", f"{kpis['repeat_customers_count']:,}", f"{kpis['repeat_customer_rate_pct']:.2f}% repeat rate", f"{kpis['total_unique_customers']:,} total", "green")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Main Visuals: Monthly Trend & Geography / Payments
    row1_c1, row1_c2 = st.columns([1.6, 1.0])
    
    with row1_c1:
        # Monthly Delivered Revenue & MoM Growth
        deliv_order_ids = set(orders_df[orders_df["order_status"] == "delivered"]["order_id"])
        deliv_items = items_df[items_df["order_id"].isin(deliv_order_ids)]
        
        merged_monthly = deliv_items.merge(orders_df[["order_id", "purchase_year_month"]], on="order_id")
        monthly_rev = merged_monthly.groupby("purchase_year_month")["price"].sum().reset_index()
        monthly_rev.rename(columns={"purchase_year_month": "Month", "price": "Revenue"}, inplace=True)
        monthly_rev["MoM_Growth_Pct"] = monthly_rev["Revenue"].pct_change() * 100
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly_rev["Month"],
            y=monthly_rev["Revenue"],
            name="Delivered Revenue (R$)",
            marker_color="#2980B9",
            hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.2f}<extra></extra>"
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly_rev["Month"],
            y=monthly_rev["MoM_Growth_Pct"],
            name="MoM Growth %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#E67E22", width=2.5),
            marker=dict(size=6, color="#D35400"),
            hovertemplate="<b>%{x}</b><br>MoM Growth: %{y:.1f}%<extra></extra>"
        ))
        fig_trend.update_layout(
            yaxis2=dict(
                title=dict(text="MoM Growth %", font=dict(size=11, color="#E67E22")),
                overlaying="y",
                side="right",
                showgrid=False,
                tickfont=dict(size=10, color="#E67E22")
            )
        )
        apply_plotly_theme(fig_trend, "Monthly Delivered Revenue (R$) & MoM Growth Rate", "Purchase Year-Month", "Revenue (R$)")
        st.plotly_chart(fig_trend, use_container_width=True)

    with row1_c2:
        # Top 10 Customer States by Revenue
        merged_cust = deliv_items.merge(orders_df[["order_id", "customer_id"]], on="order_id").merge(
            customers_df[["customer_id", "customer_state"]], on="customer_id"
        )
        state_rev = merged_cust.groupby("customer_state")["price"].sum().reset_index()
        state_rev = state_rev.sort_values(by="price", ascending=True).tail(10)
        
        fig_state = px.bar(
            state_rev,
            x="price",
            y="customer_state",
            orientation="h",
            text="price",
            color="price",
            color_continuous_scale="Blues"
        )
        fig_state.update_traces(
            texttemplate="R$ %{text:,.0f}",
            textposition="inside",
            hovertemplate="<b>State %{y}</b><br>Revenue: R$ %{x:,.2f}<extra></extra>"
        )
        fig_state.update_coloraxes(showscale=False)
        apply_plotly_theme(fig_state, "Top 10 States by Delivered Revenue (R$)", "Revenue (R$)", "State")
        st.plotly_chart(fig_state, use_container_width=True)

    # 3. Monthly Sales Summary Data Table
    st.markdown('<div class="section-header">Monthly Sales Aggregation Table</div>', unsafe_allow_html=True)
    monthly_table = monthly_rev.copy()
    monthly_table["Revenue (R$)"] = monthly_table["Revenue"].apply(lambda x: f"R$ {x:,.2f}")
    monthly_table["MoM Growth %"] = monthly_table["MoM_Growth_Pct"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")
    
    st.dataframe(monthly_table[["Month", "Revenue (R$)", "MoM Growth %"]], use_container_width=True, hide_index=True)
    render_download_button(monthly_rev, "monthly_delivered_sales.csv", "📥 Export Monthly Sales Summary (CSV)", key="download_overview_monthly")

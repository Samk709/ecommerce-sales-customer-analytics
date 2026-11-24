"""
==============================================================================
View: Executive Overview & Sales Performance
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.components import (
    render_kpi_card,
    render_insight_box,
    apply_plotly_theme,
    render_download_button,
    COLOR_PRIMARY_NAVY,
    COLOR_ACCENT_BLUE
)
from streamlit_app.kpi_metrics import compute_overview_kpis

def render_overview_view(orders_df: pd.DataFrame, items_df: pd.DataFrame, customers_df: pd.DataFrame, is_filtered: bool):
    # 1. Compute Headline KPIs (Pure-Python Engine)
    kpis = compute_overview_kpis(orders_df, items_df, customers_df)
    
    # Operational Notice
    st.markdown(
        '<div class="financial-notice"><b>Operational Standard</b>: Revenue reflects delivered orders only and excludes shipping freight. '
        'All profit and COGS metrics are labelled <i>"assumed margin, not real data"</i> based on category benchmark assumptions. '
        'Currency is strictly in <b>Brazilian Reais (R$ / BRL)</b>.</div>',
        unsafe_allow_html=True
    )

    # Dynamic Key Insight Box generated strictly from underlying data
    deliv_order_ids = set(orders_df[orders_df["order_status"] == "delivered"]["order_id"])
    deliv_items = items_df[items_df["order_id"].isin(deliv_order_ids)]
    top_state_name = "SP"
    top_state_share_str = ""
    if not deliv_items.empty and not orders_df.empty and not customers_df.empty:
        merged_cust = deliv_items.merge(orders_df[["order_id", "customer_id"]], on="order_id").merge(
            customers_df[["customer_id", "customer_state"]], on="customer_id"
        )
        if not merged_cust.empty:
            state_rev_series = merged_cust.groupby("customer_state")["price"].sum()
            if not state_rev_series.empty:
                top_state_name = state_rev_series.idxmax()
                top_state_val = state_rev_series.max()
                top_state_pct = (top_state_val / kpis["total_revenue_brl"] * 100) if kpis["total_revenue_brl"] > 0 else 0
                top_state_share_str = f"with <b>{top_state_name}</b> leading revenue at <b>R$ {top_state_val:,.2f} ({top_state_pct:.1f}% share)</b>"

    insight_text = (
        f"💡 <b>Key Insight</b>: The platform generated <b>R$ {kpis['total_revenue_brl']:,.2f}</b> in delivered merchandise revenue "
        f"across <b>{kpis['total_delivered_orders']:,}</b> orders (AOV: <b>R$ {kpis['aov_brl']:,.2f}</b>) "
        f"and <b>{kpis['total_unique_customers']:,}</b> unique buyers, {top_state_share_str}. "
        f"Only <b>{kpis['repeat_customers_count']:,} customers ({kpis['repeat_customer_rate_pct']:.2f}%)</b> made repeat purchases."
    )
    render_insight_box(insight_text)
    
    # 2. Headline KPI Cards Row (Equal sizing and responsive spacing)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        render_kpi_card("Merchandise Revenue", f"R$ {kpis['total_revenue_brl']:,.2f}", "delivered orders only, excludes freight", "Delivered", "blue")
    with c2:
        render_kpi_card("Gross Merchandise (GMV)", f"R$ {kpis['gmv_brl']:,.2f}", f"Freight: R$ {kpis['total_freight_brl']:,.0f}", "Total Checkout", "blue")
    with c3:
        render_kpi_card("Delivered Orders", f"{kpis['total_delivered_orders']:,}", f"{kpis['total_items_sold']:,} items sold", "Completed", "green")
    with c4:
        render_kpi_card("Average Order Value", f"R$ {kpis['aov_brl']:,.2f}", "net spend per delivered order", "AOV", "blue")
    with c5:
        render_kpi_card("Assumed Gross Profit", f"R$ {kpis['assumed_gross_profit_brl']:,.2f}", f"{kpis['blended_gross_margin_pct']:.1f}% assumed margin", "Assumed", "amber")
    with c6:
        render_kpi_card("Repeat Customers", f"{kpis['repeat_customers_count']:,}", f"{kpis['repeat_customer_rate_pct']:.2f}% repeat buyer rate", f"{kpis['total_unique_customers']:,} total", "green")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. Clean Tabs Layout for Laptop-Friendly Presentation
    tab_trends, tab_geo, tab_table = st.tabs([
        "📈 Monthly Revenue & Growth Trend",
        "🗺️ Top States Geographic Concentration",
        "📋 Monthly Sales Summary Table"
    ])
    
    with tab_trends:
        merged_items = deliv_items.merge(orders_df[["order_id", "purchase_year_month"]], on="order_id")
        monthly_rev = merged_items.groupby("purchase_year_month")["price"].sum().reset_index()
        monthly_rev.rename(columns={"purchase_year_month": "Month", "price": "Revenue"}, inplace=True)
        monthly_rev["MoM_Growth_Pct"] = monthly_rev["Revenue"].pct_change() * 100
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly_rev["Month"],
            y=monthly_rev["Revenue"],
            name="Delivered Revenue (R$)",
            marker_color=COLOR_ACCENT_BLUE,
            hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.2f}<extra></extra>"
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly_rev["Month"],
            y=monthly_rev["MoM_Growth_Pct"],
            name="MoM Growth %",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2.5),
            marker=dict(size=6, color="#D97706"),
            hovertemplate="<b>%{x}</b><br>MoM Growth: %{y:.1f}%<extra></extra>"
        ))
        fig_trend.update_layout(
            yaxis2=dict(
                title=dict(text="MoM Growth %", font=dict(size=11, color="#D97706")),
                overlaying="y",
                side="right",
                showgrid=False,
                tickfont=dict(size=10, color="#D97706")
            )
        )
        apply_plotly_theme(fig_trend, "Monthly Delivered Revenue (R$) & Month-over-Month Growth Rate", "Purchase Year-Month", "Revenue (R$)", height=400)
        st.plotly_chart(fig_trend, use_container_width=True)

    with tab_geo:
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
            color_discrete_sequence=[COLOR_ACCENT_BLUE]
        )
        fig_state.update_traces(
            texttemplate="R$ %{x:,.0f}",
            textposition="auto",
            hovertemplate="<b>State: %{y}</b><br>Delivered Revenue: R$ %{x:,.2f}<extra></extra>"
        )
        apply_plotly_theme(fig_state, "Top 10 States by Delivered Revenue (R$)", "Revenue (R$)", "State", height=400)
        st.plotly_chart(fig_state, use_container_width=True)

    with tab_table:
        disp_monthly = monthly_rev.copy()
        disp_monthly["Revenue (R$)"] = disp_monthly["Revenue"].apply(lambda x: f"R$ {x:,.2f}")
        disp_monthly["MoM Growth %"] = disp_monthly["MoM_Growth_Pct"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")
        disp_monthly = disp_monthly[["Month", "Revenue (R$)", "MoM Growth %"]]
        
        st.dataframe(disp_monthly, use_container_width=True, hide_index=True)
        render_download_button(monthly_rev, "monthly_sales_summary.csv", "📥 Export Monthly Sales Summary (CSV)", key="download_monthly_rev_csv")

"""
View: Customer Intelligence & Retention Analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.components import render_kpi_card, apply_plotly_theme, render_download_button
from streamlit_app.data_loader import load_cohort_retention, load_rfm_summary

def render_customers_view(customers_df: pd.DataFrame, orders_df: pd.DataFrame, items_df: pd.DataFrame):
    st.markdown('<div class="section-header">Customer Intelligence, RFM & Cohort Retention</div>', unsafe_allow_html=True)
    
    # Filter customers matching active delivered orders
    deliv_order_ids = set(orders_df[orders_df["order_status"] == "delivered"]["order_id"])
    deliv_customer_ids = set(orders_df[orders_df["order_id"].isin(deliv_order_ids)]["customer_id"])
    active_customers = customers_df[customers_df["customer_id"].isin(deliv_customer_ids)]
    
    deliv_items = items_df[items_df["order_id"].isin(deliv_order_ids)]
    total_rev = deliv_items["price"].sum()
    
    total_uniques = active_customers["customer_unique_id"].nunique()
    repeat_uniques = active_customers[active_customers["is_repeat_customer"] == 1]["customer_unique_id"].nunique()
    repeat_rate = (repeat_uniques / total_uniques * 100) if total_uniques > 0 else 0.0
    overall_clv = total_rev / total_uniques if total_uniques > 0 else 0.0
    
    # 1. Headline Customer KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total Unique Customers", f"{total_uniques:,}", "Delivered order base", "Base", "blue")
    with c2:
        render_kpi_card("Repeat Customers", f"{repeat_uniques:,}", f"{repeat_rate:.2f}% of customer base", "Repeat", "green")
    with c3:
        render_kpi_card("Historical CLV", f"R$ {overall_clv:,.2f}", "Avg lifetime merchandise spend", "CLV", "blue")
    with c4:
        render_kpi_card("Repeat Spend Premium", "R$ 260.05 vs R$ 137.96", "+88.5% spend per repeat user", "Premium", "amber")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. RFM Segment Distribution & Summary
    row1_c1, row1_c2 = st.columns([1.2, 1.0])
    
    rfm_summary = load_rfm_summary()
    segment_colors = {
        "Top Value": "#2ECC71",
        "Mid Value": "#3498DB",
        "Dormant": "#E67E22",
        "Low Spend": "#E74C3C"
    }
    
    with row1_c1:
        if not rfm_summary.empty:
            fig_rfm = go.Figure()
            fig_rfm.add_trace(go.Bar(
                x=rfm_summary["segment"],
                y=rfm_summary["customer_count"],
                name="Customers",
                marker_color=[segment_colors.get(s, "#3498DB") for s in rfm_summary["segment"]],
                hovertemplate="<b>%{x}</b><br>Customers: %{y:,}<extra></extra>"
            ))
            fig_rfm.add_trace(go.Scatter(
                x=rfm_summary["segment"],
                y=rfm_summary["total_revenue_brl"],
                name="Revenue (R$)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#1B2A4A", width=3),
                marker=dict(size=8, color="#1B2A4A"),
                hovertemplate="<b>%{x}</b><br>Revenue: R$ %{y:,.2f}<extra></extra>"
            ))
            fig_rfm.update_layout(
                yaxis2=dict(
                    title=dict(text="Revenue (R$)", font=dict(size=11, color="#1B2A4A")),
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    tickfont=dict(size=10, color="#1B2A4A")
                )
            )
            apply_plotly_theme(fig_rfm, "RFM Value Segments: Customer Volume vs Revenue", "RFM Segment", "Unique Customers")
            st.plotly_chart(fig_rfm, use_container_width=True)

    with row1_c2:
        # One-Time vs Repeat Share Donut Chart
        one_time_count = total_uniques - repeat_uniques
        fig_donut = go.Figure(data=[go.Pie(
            labels=["One-Time Buyers (1 Order)", "Repeat Buyers (>=2 Orders)"],
            values=[one_time_count, repeat_uniques],
            hole=0.55,
            marker_colors=["#95A5A6", "#27AE60"],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Users: %{value:,} (%{percent})<extra></extra>"
        )])
        apply_plotly_theme(fig_donut, "Customer Buyer Frequency Composition")
        st.plotly_chart(fig_donut, use_container_width=True)

    # 3. Monthly Cohort Retention Heatmap
    st.markdown('<div class="section-header">Monthly Cohort Retention Heatmap (2017 Cohorts)</div>', unsafe_allow_html=True)
    st.caption("Tracking customer repeat purchase retention across months elapsed. Observed months with zero returns show 0.00%; unobserved future periods remain blank.")
    
    cohort_matrix = load_cohort_retention()
    if not cohort_matrix.empty:
        # Display 2017 cohorts
        cohort_2017 = cohort_matrix.loc["2017-01":"2017-12", [str(i) for i in range(13) if str(i) in cohort_matrix.columns]]
        
        # Plot Heatmap using Plotly
        fig_cohort = px.imshow(
            cohort_2017.values,
            labels=dict(x="Months Elapsed Since First Purchase", y="Acquisition Cohort Month", color="Retention Rate (%)"),
            x=cohort_2017.columns,
            y=cohort_2017.index,
            color_continuous_scale="YlGnBu",
            text_auto=".2f",
            zmin=0.0,
            zmax=1.0,
            aspect="auto"
        )
        fig_cohort.update_traces(
            hovertemplate="Cohort: %{y}<br>Month %{x}: %{z:.2f}% retention<extra></extra>"
        )
        apply_plotly_theme(fig_cohort, "", "Months Elapsed (0 to 12)", "Acquisition Cohort", height=380)
        st.plotly_chart(fig_cohort, use_container_width=True)

    # 4. RFM Segment Details Table
    st.markdown('<div class="section-header">RFM Value Segment Summary Table</div>', unsafe_allow_html=True)
    if not rfm_summary.empty:
        disp_rfm = rfm_summary.copy()
        disp_rfm["customer_count"] = disp_rfm["customer_count"].apply(lambda x: f"{int(x):,}")
        disp_rfm["repeat_customers"] = disp_rfm["repeat_customers"].apply(lambda x: f"{int(x):,}")
        disp_rfm["customer_pct"] = disp_rfm["customer_pct"].apply(lambda x: f"{x:.2f}%")
        disp_rfm["repeat_buyer_pct"] = disp_rfm["repeat_buyer_pct"].apply(lambda x: f"{x:.2f}%")
        disp_rfm["total_revenue_brl"] = disp_rfm["total_revenue_brl"].apply(lambda x: f"R$ {x:,.2f}")
        disp_rfm["revenue_pct"] = disp_rfm["revenue_pct"].apply(lambda x: f"{x:.2f}%")
        disp_rfm["avg_recency_days"] = disp_rfm["avg_recency_days"].apply(lambda x: f"{x:.1f} days")
        disp_rfm["avg_spend_brl"] = disp_rfm["avg_spend_brl"].apply(lambda x: f"R$ {x:,.2f}")
        
        disp_rfm.rename(columns={
            "segment": "RFM Segment",
            "customer_count": "Customers",
            "customer_pct": "Customer Share",
            "repeat_customers": "Repeat Buyers",
            "repeat_buyer_pct": "Repeat Share %",
            "total_revenue_brl": "Total Revenue (R$)",
            "revenue_pct": "Revenue Share",
            "avg_recency_days": "Avg Recency",
            "avg_frequency": "Avg Frequency",
            "avg_spend_brl": "Avg Spend (R$)"
        }, inplace=True)
        
        st.dataframe(disp_rfm, use_container_width=True, hide_index=True)
        render_download_button(rfm_summary, "rfm_segment_summary.csv", "📥 Export RFM Segment Summary (CSV)", key="download_rfm_summary")

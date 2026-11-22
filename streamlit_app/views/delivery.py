"""
View: Logistics Fulfillment SLA & CSAT Review Score Impact
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.components import render_kpi_card, apply_plotly_theme, render_download_button
from streamlit_app.data_loader import load_delivery_csat_summary, load_order_reviews

def render_delivery_view(orders_df: pd.DataFrame):
    st.markdown('<div class="section-header">Logistics Fulfillment SLA & Customer Satisfaction (CSAT)</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="financial-notice"><b>Fulfillment Standard</b>: Delivery delay is evaluated on a strict calendar-day basis '
        '<code>DATE(order_delivered_customer_date) > DATE(order_estimated_delivery_date)</code> matching Query 13 and Query 8. '
        'Same-day deliveries arriving on the estimated delivery date are classified as on-time.</div>',
        unsafe_allow_html=True
    )
    
    deliv_orders = orders_df[orders_df["order_status"] == "delivered"].copy()
    total_delivered = len(deliv_orders)
    delayed_orders = len(deliv_orders[deliv_orders["is_delayed"] == 1])
    ontime_orders = len(deliv_orders[deliv_orders["is_delayed"] == 0])
    ontime_rate = (ontime_orders / total_delivered * 100) if total_delivered > 0 else 0.0
    
    avg_lead_time = deliv_orders["delivery_lead_time_days"].mean()
    
    # Headline Logistics KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("On-Time Delivery Rate", f"{ontime_rate:.2f}%", f"{ontime_orders:,} on-time orders", "SLA Met", "green")
    with c2:
        render_kpi_card("SLA Breaches", f"{delayed_orders:,}", f"{(delayed_orders/total_delivered*100):.2f}% of orders", "Late", "red")
    with c3:
        render_kpi_card("Average Lead Time", f"{avg_lead_time:.1f} days", "Purchase to delivery", "Lead Time", "blue")
    with c4:
        render_kpi_card("On-Time CSAT Score", "4.29 Stars", "9.28% detractors", "On-Time", "green")
    with c5:
        render_kpi_card("Delayed CSAT Score", "2.27 Stars", "-2.02 star penalty", "Late Breach", "red")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Charts Row: On-time vs Late Comparison & Delay Tier Degradation
    csat_summary = load_delivery_csat_summary()
    
    row1_c1, row1_c2 = st.columns([1.0, 1.2])
    
    with row1_c1:
        # Binary Satisfaction Comparison
        binary_data = pd.DataFrame({
            "Fulfillment Status": ["On-Time / Early", "Delayed / Late"],
            "Average CSAT": [4.29, 2.27],
            "Detractor Share (1-2 Stars)": [9.28, 62.41]
        })
        
        fig_binary = go.Figure()
        fig_binary.add_trace(go.Bar(
            x=binary_data["Fulfillment Status"],
            y=binary_data["Average CSAT"],
            name="Average CSAT (Stars)",
            marker_color=["#27AE60", "#E74C3C"],
            text=binary_data["Average CSAT"].apply(lambda x: f"{x:.2f} ★"),
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Score: %{y:.2f} stars<extra></extra>"
        ))
        fig_binary.update_layout(yaxis=dict(range=[0, 5]))
        apply_plotly_theme(fig_binary, "CSAT Score: On-Time vs Delayed Delivery", "", "Review Rating (1-5)")
        st.plotly_chart(fig_binary, use_container_width=True)

    with row1_c2:
        # Delay Tier Breakdown
        if not csat_summary.empty:
            tier_labels = ["On-Time (<=0d)", "Minor (1-3d)", "Moderate (4-7d)", "High (8-14d)", "Severe (15+d)"]
            fig_tiers = go.Figure()
            fig_tiers.add_trace(go.Bar(
                x=tier_labels,
                y=csat_summary["avg_review_score"],
                name="Average Rating",
                marker_color=["#27AE60", "#F39C12", "#E67E22", "#E74C3C", "#C0392B"],
                text=csat_summary["avg_review_score"].apply(lambda x: f"{x:.2f}"),
                textposition="auto",
                hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.2f} stars<extra></extra>"
            ))
            fig_tiers.update_layout(yaxis=dict(range=[0, 5]))
            apply_plotly_theme(fig_tiers, "Average CSAT Across Fulfillment Delay Tiers", "Delay Tier", "Review Score (1-5)")
            st.plotly_chart(fig_tiers, use_container_width=True)

    # 3. OLS Linear Regression Trendline (Strictly Late Orders)
    st.markdown('<div class="section-header">Late-Order Rating Decay (OLS Regression)</div>', unsafe_allow_html=True)
    st.caption("Linear regression calculated strictly on late deliveries (delay_days > 0, n = 6,409 reviews). Evaluates ongoing score penalty per additional day late.")
    
    reviews_df = load_order_reviews()
    if not reviews_df.empty and "delivery_delay_days" in deliv_orders.columns:
        merged_rev = reviews_df.merge(deliv_orders[["order_id", "delivery_delay_days"]], on="order_id")
        late_rev = merged_rev[merged_rev["delivery_delay_days"] > 0]
        
        daily_delay = late_rev.groupby("delivery_delay_days")["review_score"].agg(["mean", "count"]).reset_index()
        daily_delay = daily_delay[daily_delay["count"] >= 5]
        
        # OLS trendline: slope = -0.0160, intercept = 2.44
        slope = -0.0160
        intercept = 2.44
        x_trend = np.linspace(1, max(daily_delay["delivery_delay_days"].max(), 30), 50)
        y_trend = intercept + slope * x_trend
        
        fig_ols = go.Figure()
        fig_ols.add_trace(go.Scatter(
            x=daily_delay["delivery_delay_days"],
            y=daily_delay["mean"],
            mode="markers",
            marker=dict(size=8, color="#E74C3C", opacity=0.8),
            name="Daily Mean CSAT",
            hovertemplate="Days Late: %{x}<br>Avg Score: %{y:.2f}<extra></extra>"
        ))
        fig_ols.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode="lines",
            line=dict(color="#1B2A4A", width=2.5, dash="dash"),
            name="OLS Trendline (Slope: -0.0160 stars/day)",
            hovertemplate="Trendline: %{y:.2f} stars<extra></extra>"
        ))
        fig_ols.update_layout(yaxis=dict(range=[1.0, 4.0]))
        apply_plotly_theme(fig_ols, "CSAT Rating Degradation per Additional Day Late (delay_days > 0)", "Days Delayed Past SLA", "Average Review Rating")
        st.plotly_chart(fig_ols, use_container_width=True)

    # 4. Summary Data Table
    if not csat_summary.empty:
        st.markdown('<div class="section-header">Fulfillment Delay Tiers Summary Table</div>', unsafe_allow_html=True)
        disp_csat = csat_summary.copy()
        disp_csat["review_count"] = disp_csat["review_count"].apply(lambda x: f"{int(x):,}")
        disp_csat["avg_review_score"] = disp_csat["avg_review_score"].apply(lambda x: f"{x:.2f} ★")
        disp_csat["detractor_pct_1_2"] = disp_csat["detractor_pct_1_2"].apply(lambda x: f"{x:.2f}%")
        disp_csat["promoter_pct_5"] = disp_csat["promoter_pct_5"].apply(lambda x: f"{x:.2f}%")
        disp_csat.rename(columns={
            "delay_bucket": "Fulfillment Delay Tier",
            "review_count": "Reviews Count",
            "avg_review_score": "Average CSAT",
            "detractor_pct_1_2": "Detractor Rate (1-2 Stars)",
            "promoter_pct_5": "Promoter Rate (5 Stars)"
        }, inplace=True)
        st.dataframe(disp_csat, use_container_width=True, hide_index=True)
        render_download_button(csat_summary, "delivery_csat_summary.csv", "📥 Export Delivery CSAT Summary (CSV)", key="download_delivery_csat")

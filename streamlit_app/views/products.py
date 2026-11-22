"""
View: Products & Category Intelligence
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.components import render_kpi_card, apply_plotly_theme, render_download_button
from streamlit_app.data_loader import load_pareto_summary

def render_products_view(orders_df: pd.DataFrame, items_df: pd.DataFrame, products_df: pd.DataFrame):
    st.markdown('<div class="section-header">Products & Macro Category Profitability</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="financial-notice"><b>Financial Notice</b>: Product cost and profitability figures are calculated using benchmark category margins '
        'from <code>config/margin_assumptions.yaml</code> and labelled <b>"assumed margin, not real data"</b>. '
        'Revenue reflects delivered items only in Brazilian Reais (R$).</div>',
        unsafe_allow_html=True
    )
    
    # 1. Category Profitability Breakdown
    deliv_order_ids = set(orders_df[orders_df["order_status"] == "delivered"]["order_id"])
    deliv_items = items_df[items_df["order_id"].isin(deliv_order_ids)]
    
    merged_prod = deliv_items.merge(
        products_df[["product_id", "product_category_name_english", "category_group"]],
        on="product_id"
    )
    
    cat_summary = merged_prod.groupby("category_group").agg(
        items_sold=("order_item_id", "count"),
        total_revenue_brl=("price", "sum"),
        assumed_cogs_brl=("assumed_cogs_brl", "sum"),
        assumed_gross_profit_brl=("assumed_gross_profit_brl", "sum")
    ).reset_index()
    
    cat_summary["blended_gross_margin_pct"] = (cat_summary["assumed_gross_profit_brl"] / cat_summary["total_revenue_brl"]) * 100
    cat_summary = cat_summary.sort_values(by="total_revenue_brl", ascending=False).reset_index(drop=True)
    
    # KPI Cards Row
    total_rev = cat_summary["total_revenue_brl"].sum()
    total_gp = cat_summary["assumed_gross_profit_brl"].sum()
    blended_margin = (total_gp / total_rev) * 100 if total_rev > 0 else 0.0
    top_cat = cat_summary.iloc[0]["category_group"] if len(cat_summary) > 0 else "N/A"
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Merchandise Revenue", f"R$ {total_rev:,.2f}", "Across filtered categories", "Sales", "blue")
    with c2:
        render_kpi_card("Assumed Gross Profit", f"R$ {total_gp:,.2f}", "assumed margin, not real data", "Profit", "green")
    with c3:
        render_kpi_card("Blended Gross Margin", f"{blended_margin:.2f}%", "assumed margin, not real data", "Margin", "amber")
    with c4:
        render_kpi_card("Top Selling Sector", top_cat, f"R$ {cat_summary.iloc[0]['total_revenue_brl']:,.0f}" if len(cat_summary) > 0 else "", "Leader", "blue")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Charts Row: Revenue vs Gross Profit & Pareto Curve
    col_chart1, col_chart2 = st.columns([1.3, 1.0])
    
    with col_chart1:
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            y=cat_summary["category_group"],
            x=cat_summary["total_revenue_brl"],
            name="Revenue (R$)",
            orientation="h",
            marker_color="#2980B9",
            hovertemplate="<b>%{y}</b><br>Revenue: R$ %{x:,.2f}<extra></extra>"
        ))
        fig_cat.add_trace(go.Bar(
            y=cat_summary["category_group"],
            x=cat_summary["assumed_gross_profit_brl"],
            name="Assumed Gross Profit (R$)",
            orientation="h",
            marker_color="#27AE60",
            hovertemplate="<b>%{y}</b><br>Gross Profit: R$ %{x:,.2f}<extra></extra>"
        ))
        fig_cat.update_layout(
            barmode="group",
            yaxis=dict(autorange="reversed")
        )
        apply_plotly_theme(fig_cat, "Revenue vs Assumed Gross Profit by Macro Category", "Amount (R$)", "Category Group", height=420)
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_chart2:
        pareto_df = load_pareto_summary()
        if not pareto_df.empty:
            total_skus = len(pareto_df)
            top_80_skus = len(pareto_df[pareto_df["cum_revenue_pct"] <= 80.0]) + 1
            top_80_pct = (top_80_skus / total_skus) * 100
            
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Scatter(
                x=pareto_df["cum_product_pct"],
                y=pareto_df["cum_revenue_pct"],
                mode="lines",
                line=dict(color="#2980B9", width=2.5),
                name="Cumulative Revenue %",
                hovertemplate="Top %{x:.1f}% Products: %{y:.1f}% Revenue<extra></extra>"
            ))
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="#E74C3C", annotation_text="80% Revenue Cutoff", annotation_position="bottom right")
            fig_pareto.add_vline(x=top_80_pct, line_dash="dash", line_color="#27AE60", annotation_text=f"Top {top_80_pct:.1f}% SKUs ({top_80_skus:,})", annotation_position="top left")
            
            apply_plotly_theme(fig_pareto, "Product Pareto Curve (80/20 Distribution)", "Cumulative % of Unique Products", "Cumulative % of Revenue", height=420)
            st.plotly_chart(fig_pareto, use_container_width=True)

    # 3. Best-Selling Products Table
    st.markdown('<div class="section-header">Top 20 Best-Selling Products</div>', unsafe_allow_html=True)
    top_products = merged_prod.groupby(
        ["product_id", "product_category_name_english", "category_group"]
    ).agg(
        units_sold=("order_item_id", "count"),
        total_revenue_brl=("price", "sum"),
        assumed_gp_brl=("assumed_gross_profit_brl", "sum")
    ).reset_index().sort_values(by="total_revenue_brl", ascending=False).head(20)
    
    top_products["assumed_margin_pct"] = (top_products["assumed_gp_brl"] / top_products["total_revenue_brl"]) * 100
    
    display_prod = top_products.copy()
    display_prod["total_revenue_brl"] = display_prod["total_revenue_brl"].apply(lambda x: f"R$ {x:,.2f}")
    display_prod["assumed_gp_brl"] = display_prod["assumed_gp_brl"].apply(lambda x: f"R$ {x:,.2f}")
    display_prod["assumed_margin_pct"] = display_prod["assumed_margin_pct"].apply(lambda x: f"{x:.1f}%")
    display_prod.rename(columns={
        "product_id": "Product SKU",
        "product_category_name_english": "Category",
        "category_group": "Macro Sector",
        "units_sold": "Units Sold",
        "total_revenue_brl": "Revenue (R$)",
        "assumed_gp_brl": "Gross Profit (R$) [Assumed]",
        "assumed_margin_pct": "Margin % [Assumed]"
    }, inplace=True)
    
    st.dataframe(display_prod, use_container_width=True, hide_index=True)
    render_download_button(top_products, "top_selling_products.csv", "📥 Export Top Selling Products (CSV)", key="download_products_table")

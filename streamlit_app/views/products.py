"""
==============================================================================
View: Products & Category Intelligence
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, Streamlit, Plotly
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_app.components import (
    render_kpi_card,
    render_insight_box,
    apply_plotly_theme,
    render_download_button,
    PLOTLY_CONFIG,
    COLOR_PRIMARY_NAVY,
    COLOR_ACCENT_BLUE,
    COLOR_SUCCESS
)
from streamlit_app.data_loader import load_pareto_summary

def render_products_view(orders_df: pd.DataFrame, items_df: pd.DataFrame, products_df: pd.DataFrame):
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
    
    total_rev = cat_summary["total_revenue_brl"].sum()
    total_gp = cat_summary["assumed_gross_profit_brl"].sum()
    blended_margin = (total_gp / total_rev) * 100 if total_rev > 0 else 0.0
    top_cat = cat_summary.iloc[0]["category_group"] if len(cat_summary) > 0 else "N/A"

    # Dynamic Key Insight Box generated strictly from underlying data
    pareto_insight_str = ""
    pareto_df = load_pareto_summary()
    if not pareto_df.empty:
        total_skus = len(pareto_df)
        top_80_skus = len(pareto_df[pareto_df["cum_revenue_pct"] <= 80.0]) + 1
        top_80_pct = (top_80_skus / total_skus) * 100
        pareto_insight_str = f" Catalog revenue is heavily concentrated: <b>{top_80_skus:,} SKUs ({top_80_pct:.1f}% of catalog)</b> generate 80% of total sales."

    if len(cat_summary) > 0:
        top_row = cat_summary.iloc[0]
        top_rev = top_row["total_revenue_brl"]
        top_share = (top_rev / total_rev * 100) if total_rev > 0 else 0
        top_margin = top_row["blended_gross_margin_pct"]
        insight_text = (
            f"💡 <b>Key Insight</b>: <b>{top_cat}</b> is the leading sector, driving "
            f"<b>R$ {top_rev:,.2f} ({top_share:.1f}% of sales)</b> with an assumed margin of <b>{top_margin:.1f}%</b>. "
            f"Overall platform blended gross margin is <b>{blended_margin:.2f}%</b> (R$ {total_gp:,.2f} gross profit).{pareto_insight_str}"
        )
    else:
        insight_text = "💡 <b>Key Insight</b>: Products and category margin overview."
    render_insight_box(insight_text)

    # 2. KPI Cards Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Merchandise Revenue", f"R$ {total_rev:,.2f}", "delivered items across filtered categories", "Sales", "blue")
    with c2:
        render_kpi_card("Assumed Gross Profit", f"R$ {total_gp:,.2f}", "assumed margin, not real data", "Profit", "green")
    with c3:
        render_kpi_card("Blended Gross Margin", f"{blended_margin:.2f}%", "assumed margin benchmark", "Margin", "amber")
    with c4:
        render_kpi_card("Top Selling Sector", top_cat, f"R$ {cat_summary.iloc[0]['total_revenue_brl']:,.0f}" if len(cat_summary) > 0 else "", "Leader", "blue")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. Clean Tabs Layout for Laptop-Friendly Presentation
    tab_margins, tab_pareto, tab_skus = st.tabs([
        "📊 Sector Profitability & Margins",
        "⚖️ 80/20 Product Pareto Curve",
        "🏆 Top 20 Best-Selling Products"
    ])
    
    with tab_margins:
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            y=cat_summary["category_group"],
            x=cat_summary["total_revenue_brl"],
            name="Revenue (R$)",
            orientation="h",
            marker_color=COLOR_ACCENT_BLUE,
            hovertemplate="<b>%{y}</b><br>Revenue: R$ %{x:,.2f}<extra></extra>"
        ))
        fig_cat.add_trace(go.Bar(
            y=cat_summary["category_group"],
            x=cat_summary["assumed_gross_profit_brl"],
            name="Assumed Gross Profit (R$)",
            orientation="h",
            marker_color=COLOR_SUCCESS,
            hovertemplate="<b>%{y}</b><br>Gross Profit: R$ %{x:,.2f}<extra></extra>"
        ))
        fig_cat.update_layout(
            barmode="group",
            yaxis=dict(autorange="reversed")
        )
        apply_plotly_theme(fig_cat, "Delivered Revenue vs Assumed Gross Profit by Macro Category", "Amount (R$)", "Category Group", height=420)
        st.plotly_chart(fig_cat, use_container_width=True, config=PLOTLY_CONFIG)

    with tab_pareto:
        if not pareto_df.empty:
            if "cum_product_pct" not in pareto_df.columns:
                pareto_df["cum_product_pct"] = (pd.Series(range(1, len(pareto_df) + 1), index=pareto_df.index) / len(pareto_df)) * 100
            
            total_skus = len(pareto_df)
            top_80_skus = len(pareto_df[pareto_df["cum_revenue_pct"] <= 80.0]) + 1
            top_80_pct = (top_80_skus / total_skus) * 100
            
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Scatter(
                x=pareto_df["cum_product_pct"],
                y=pareto_df["cum_revenue_pct"],
                mode="lines",
                line=dict(color=COLOR_ACCENT_BLUE, width=2.5),
                name="Cumulative Revenue %",
                hovertemplate="Products: %{x:.1f}%<br>Cum Revenue: %{y:.1f}%<extra></extra>"
            ))
            # 80% Horizontal Cutoff
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="#EF4444", annotation_text="80% Revenue Cutoff", annotation_position="top right")
            # Vertical Cutoff
            fig_pareto.add_vline(x=top_80_pct, line_dash="dash", line_color="#10B981", annotation_text=f"Top {top_80_pct:.1f}% SKUs ({top_80_skus:,})", annotation_position="top left")
            
            apply_plotly_theme(fig_pareto, "Product Pareto Curve (80/20 Distribution)", "Cumulative % of Unique Products", "Cumulative % of Revenue", height=420)
            st.plotly_chart(fig_pareto, use_container_width=True, config=PLOTLY_CONFIG)

    with tab_skus:
        sku_summary = merged_prod.groupby(["product_id", "product_category_name_english", "category_group"]).agg(
            units_sold=("order_item_id", "count"),
            total_revenue=("price", "sum"),
            assumed_gross_profit=("assumed_gross_profit_brl", "sum")
        ).reset_index()
        sku_summary["margin_pct"] = (sku_summary["assumed_gross_profit"] / sku_summary["total_revenue"]) * 100
        sku_summary = sku_summary.sort_values(by="total_revenue", ascending=False).head(20).reset_index(drop=True)
        
        disp_sku = sku_summary.copy()
        disp_sku["total_revenue"] = disp_sku["total_revenue"].apply(lambda x: f"R$ {x:,.2f}")
        disp_sku["assumed_gross_profit"] = disp_sku["assumed_gross_profit"].apply(lambda x: f"R$ {x:,.2f}")
        disp_sku["margin_pct"] = disp_sku["margin_pct"].apply(lambda x: f"{x:.1f}%")
        disp_sku.rename(columns={
            "product_id": "Product SKU",
            "product_category_name_english": "Category",
            "category_group": "Macro Sector",
            "units_sold": "Units Sold",
            "total_revenue": "Revenue (R$)",
            "assumed_gross_profit": "Gross Profit (R$) [Assumed]",
            "margin_pct": "Margin % [Assumed]"
        }, inplace=True)
        
        st.dataframe(disp_sku, use_container_width=True, hide_index=True)
        render_download_button(sku_summary, "top_20_products.csv", "📥 Export Top Selling Products (CSV)", key="download_top_products_csv")

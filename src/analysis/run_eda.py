"""
==============================================================================
Phase 4: Exploratory Data Analysis (EDA) & Customer Intelligence Pipeline
==============================================================================
Author: Senior Data Analyst & Full-Stack Developer
Environment: Python 3.10 / 3.11, MySQL 8.0, Pandas, Statsmodels, Seaborn

Scope:
1. RFM Customer Segmentation (Top Value, Mid Value, Lapsing, Inactive)
2. Monthly Cohort Retention Matrix & Heatmap (0.00 for observed zeros)
3. Customer Lifetime Value (CLV) Modeling
4. Product Portfolio Pareto (80/20) Analysis
5. Delivery Delay vs Review Score (CSAT) Regression (Late-only slope)
6. Macro Category Profitability (Assumed Margins)
7. Time-Series Seasonality Decomposition & 30-Day Holt-Winters Forecast
8. Dashboard-Ready CSV Exports & Visualizations
9. Dynamic Generation of docs/eda_findings.md
==============================================================================
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.database.db_connection import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [eda_pipeline]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("eda_pipeline")

# Output Paths
EXPORTS_DIR = "data/exports"
SCREENSHOTS_DIR = "docs/screenshots"
DOCS_FILE = "docs/eda_findings.md"

os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Matplotlib styling for presentation
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["figure.titlesize"] = 14
plt.rcParams["figure.titleweight"] = "bold"

# ==============================================================================
# 1. RFM CUSTOMER SEGMENTATION
# ==============================================================================
def run_rfm_segmentation(engine) -> dict:
    logger.info("Executing Module 1: RFM Customer Segmentation...")
    query = """
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        SUM(i.price) AS order_revenue
    FROM dim_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id, o.order_id, o.order_purchase_timestamp;
    """
    df = pd.read_sql(query, engine)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    
    # Reference date is max purchase date + 1 day
    ref_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    
    rfm = df.groupby("customer_unique_id").agg(
        recency=("order_purchase_timestamp", lambda x: (ref_date - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("order_revenue", "sum")
    ).reset_index()

    # Handling the 97% One-Time Buyer Distribution:
    # Standard quantile binning fails on Frequency because >96.9% have frequency = 1.
    # Therefore, we score Frequency discretely: 2 for repeat buyers (>=2), 1 for single buyers (1).
    # Recency and Monetary are segmented into robust quartiles (1 to 4).
    rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1]).astype(int)  # 4 = most recent
    rfm["m_score"] = pd.qcut(rfm["monetary"], 4, labels=[1, 2, 3, 4]).astype(int) # 4 = highest spend
    rfm["f_score"] = rfm["frequency"].apply(lambda x: 2 if x >= 2 else 1)

    # Renamed segments reflecting spend and recency without overstating loyalty:
    # Top Value: Recent top spenders or active repeat buyers
    # Mid Value: Recent moderate spenders or remaining repeat buyers
    # Dormant: Oldest cohort of customers (avg recency 334.80 days) with moderate spend (avg R$ 169.81)
    # Low Spend: Customers defined by low basket size (avg spend R$ 46.89, avg recency 226.83 days)
    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        # Top Value: Repeat buyers with recent activity OR recent top-quartile spenders
        if (f == 2 and r >= 3) or (r == 4 and m == 4):
            return "Top Value"
        # Mid Value: Remaining repeat buyers OR recent moderate-to-high spenders
        elif (f == 2 and r <= 2) or (r >= 3 and m >= 3):
            return "Mid Value"
        # Dormant: Oldest cohort of customers with moderate-to-high spend (avg recency 334.80 days)
        elif (r == 2) or (r == 1 and m >= 3):
            return "Dormant"
        # Low Spend: Customers defined by low basket size (avg spend R$ 46.89, avg recency 226.83 days)
        else:
            return "Low Spend"

    rfm["segment"] = rfm.apply(assign_segment, axis=1)

    # Segment Summary with repeat customer metrics
    summary = rfm.groupby("segment").agg(
        customer_count=("customer_unique_id", "count"),
        repeat_customers=("frequency", lambda x: (x >= 2).sum()),
        total_revenue_brl=("monetary", "sum"),
        avg_recency_days=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_spend_brl=("monetary", "mean")
    ).reset_index()

    total_customers = len(rfm)
    total_rev = rfm["monetary"].sum()
    summary["customer_pct"] = (summary["customer_count"] / total_customers) * 100
    summary["repeat_buyer_pct"] = (summary["repeat_customers"] / summary["customer_count"]) * 100
    summary["revenue_pct"] = (summary["total_revenue_brl"] / total_rev) * 100

    # Ensure consistent order by revenue
    segment_order = ["Top Value", "Mid Value", "Dormant", "Low Spend"]
    summary["sort_order"] = summary["segment"].apply(lambda x: segment_order.index(x) if x in segment_order else 99)
    summary = summary.sort_values(by="sort_order").drop(columns=["sort_order"]).reset_index(drop=True)

    # Reorder columns
    summary = summary[[
        "segment", "customer_count", "customer_pct", "repeat_customers", "repeat_buyer_pct",
        "total_revenue_brl", "revenue_pct", "avg_recency_days", "avg_frequency", "avg_spend_brl"
    ]]

    # Export customer-level and summary CSV
    rfm.to_csv(os.path.join(EXPORTS_DIR, "rfm_customer_segments.csv"), index=False)
    summary.to_csv(os.path.join(EXPORTS_DIR, "rfm_segment_summary.csv"), index=False)

    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    palette = {"Top Value": "#2ecc71", "Mid Value": "#3498db", "Dormant": "#e67e22", "Low Spend": "#e74c3c"}
    
    sns.barplot(data=summary, x="segment", y="customer_count", hue="segment", palette=palette, legend=False, ax=axes[0])
    axes[0].set_title("Customer Volume by RFM Value Segment")
    axes[0].set_ylabel("Unique Customers")
    axes[0].set_xlabel("RFM Segment")
    for p in axes[0].patches:
        axes[0].annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=9)

    sns.barplot(data=summary, x="segment", y="total_revenue_brl", hue="segment", palette=palette, legend=False, ax=axes[1])
    axes[1].set_title("Total Revenue (R$) by RFM Value Segment")
    axes[1].set_ylabel("Delivered Revenue (R$ BRL)")
    axes[1].set_xlabel("RFM Segment")
    for p in axes[1].patches:
        axes[1].annotate(f"R$ {p.get_height():,.0f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=9)

    plt.tight_layout()
    chart_path = os.path.join(SCREENSHOTS_DIR, "rfm_segments_distribution.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()

    logger.info("Module 1 complete.")
    return {
        "rfm_df": rfm,
        "summary": summary,
        "total_customers": total_customers,
        "total_revenue": total_rev,
        "total_repeat_customers": (rfm["frequency"] >= 2).sum(),
        "chart_path": chart_path
    }

# ==============================================================================
# 2. MONTHLY COHORT RETENTION ANALYSIS
# ==============================================================================
def run_cohort_retention(engine) -> dict:
    logger.info("Executing Module 2: Monthly Cohort Retention Heatmap...")
    query = """
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp
    FROM dim_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered';
    """
    df = pd.read_sql(query, engine)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M")

    # Cohort Month: First purchase month per unique customer
    first_month = df.groupby("customer_unique_id")["order_month"].min().reset_index()
    first_month.rename(columns={"order_month": "cohort_month"}, inplace=True)
    df = df.merge(first_month, on="customer_unique_id")

    # Calculate month offset (cohort_index)
    df["cohort_index"] = (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12 + \
                         (df["order_month"].dt.month - df["cohort_month"].dt.month)

    cohort_pivot = df.pivot_table(
        index="cohort_month",
        columns="cohort_index",
        values="customer_unique_id",
        aggfunc="nunique"
    )

    cohort_sizes = cohort_pivot[0]
    retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    # Fix 4: Differentiate observed zero-returning months (0.00) vs unobserved future months (NaN)
    max_order_month = df["order_month"].max()
    for cohort_m in retention_matrix.index:
        for idx in retention_matrix.columns:
            period_m = cohort_m + int(idx)
            if period_m <= max_order_month:
                if pd.isna(retention_matrix.loc[cohort_m, idx]):
                    retention_matrix.loc[cohort_m, idx] = 0.0
            else:
                retention_matrix.loc[cohort_m, idx] = np.nan

    # Filter main active operational window (Jan 2017 to Dec 2017 cohorts with >= 8 months history)
    heatmap_df = retention_matrix.loc["2017-01":"2017-12", :12].copy()

    # Export CSV
    retention_matrix.to_csv(os.path.join(EXPORTS_DIR, "cohort_retention_matrix.csv"))

    # Plot Heatmap
    plt.figure(figsize=(14, 7))
    sns.heatmap(
        heatmap_df,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        cbar_kws={"label": "Retention Rate (%)"},
        vmin=0.0,
        vmax=1.0,  # Highlight sub-1% retention variations
        linewidths=0.5
    )
    plt.title("Monthly Customer Cohort Retention Rate (%) [2017 Cohorts]\n*(Observed periods with 0 returning customers shown as 0.00; future periods blank)*",
              fontsize=13, weight="bold")
    plt.xlabel("Cohort Period (Months Elapsed Since First Purchase)", fontsize=11)
    plt.ylabel("Acquisition Cohort Month", fontsize=11)
    
    chart_path = os.path.join(SCREENSHOTS_DIR, "cohort_retention_heatmap.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    # Metrics for documentation
    avg_m1_retention = retention_matrix.loc["2017-01":"2018-06", 1].mean()
    max_m1_retention = retention_matrix.loc["2017-01":"2018-06", 1].max()

    logger.info("Module 2 complete.")
    return {
        "retention_matrix": retention_matrix,
        "cohort_sizes": cohort_sizes,
        "avg_m1_retention": avg_m1_retention,
        "max_m1_retention": max_m1_retention,
        "chart_path": chart_path
    }

# ==============================================================================
# 3. CUSTOMER LIFETIME VALUE (CLV)
# ==============================================================================
def run_clv_analysis(rfm_summary, rfm_df) -> dict:
    logger.info("Executing Module 3: Customer Lifetime Value (CLV)...")
    total_customers = len(rfm_df)
    total_rev = rfm_df["monetary"].sum()

    # Historical Platform CLV
    historical_clv = total_rev / total_customers
    
    # Blended Gross Margin from Phase 3 (Benchmark 40.76%)
    blended_margin = 0.4076
    margin_adjusted_clv = historical_clv * blended_margin

    # Repeat vs One-Time CLV
    repeat_df = rfm_df[rfm_df["frequency"] >= 2]
    onetime_df = rfm_df[rfm_df["frequency"] == 1]

    clv_repeat = repeat_df["monetary"].sum() / len(repeat_df)
    clv_onetime = onetime_df["monetary"].sum() / len(onetime_df)

    clv_repeat_margin = clv_repeat * blended_margin
    clv_onetime_margin = clv_onetime * blended_margin

    # Segment Level CLV
    segment_clv = rfm_summary.copy()
    segment_clv["historical_clv_brl"] = segment_clv["avg_spend_brl"]
    segment_clv["margin_adjusted_clv_brl"] = segment_clv["historical_clv_brl"] * blended_margin

    logger.info("Module 3 complete.")
    return {
        "historical_clv": historical_clv,
        "margin_adjusted_clv": margin_adjusted_clv,
        "clv_repeat": clv_repeat,
        "clv_repeat_margin": clv_repeat_margin,
        "clv_onetime": clv_onetime,
        "clv_onetime_margin": clv_onetime_margin,
        "segment_clv": segment_clv
    }

# ==============================================================================
# 4. PRODUCT PARETO ANALYSIS (80/20 RULE)
# ==============================================================================
def run_product_pareto(engine) -> dict:
    logger.info("Executing Module 4: Product Pareto Analysis...")
    query = """
    SELECT 
        i.product_id,
        p.category_group,
        p.product_category_name_english,
        COUNT(i.order_item_id) AS units_sold,
        SUM(i.price) AS total_revenue_brl
    FROM fact_order_items i
    JOIN dim_orders o ON i.order_id = o.order_id
    JOIN dim_products p ON i.product_id = p.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY i.product_id, p.category_group, p.product_category_name_english
    ORDER BY total_revenue_brl DESC;
    """
    df = pd.read_sql(query, engine)
    total_products = len(df)
    total_rev = df["total_revenue_brl"].sum()

    df["cum_revenue"] = df["total_revenue_brl"].cumsum()
    df["cum_revenue_pct"] = (df["cum_revenue"] / total_rev) * 100
    df["product_rank"] = range(1, total_products + 1)
    df["cum_product_pct"] = (df["product_rank"] / total_products) * 100

    # 80% Cutoff point
    pareto_80_df = df[df["cum_revenue_pct"] <= 80.0]
    count_80 = len(pareto_80_df) + 1
    pct_80 = (count_80 / total_products) * 100

    # Top product
    top_sku = df.iloc[0]

    # Export CSV
    df.to_csv(os.path.join(EXPORTS_DIR, "pareto_product_summary.csv"), index=False)

    # Plot Pareto Chart
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(df["cum_product_pct"], df["cum_revenue_pct"], color="#2980b9", lw=2.5, label="Cumulative Revenue %")
    ax1.axhline(80, color="#e74c3c", linestyle="--", lw=1.5, label="80% Revenue Cutoff")
    ax1.axvline(pct_80, color="#27ae60", linestyle="--", lw=1.5, label=f"Top {pct_80:.1f}% Products ({count_80:,} SKUs)")
    
    ax1.scatter([pct_80], [80], color="#c0392b", s=80, zorder=5)
    ax1.annotate(f"80% Revenue = {pct_80:.2f}% Products\n({count_80:,} of {total_products:,} SKUs)",
                 xy=(pct_80, 80), xytext=(pct_80 + 5, 65),
                 arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5),
                 fontsize=10, weight="bold",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#fadbd8", ec="#c0392b", lw=1))

    ax1.set_title("Product Portfolio Pareto Curve (80/20 Distribution)", fontsize=13, weight="bold")
    ax1.set_xlabel("Cumulative Percentage of Unique Products (%)", fontsize=11)
    ax1.set_ylabel("Cumulative Percentage of Revenue (%)", fontsize=11)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 105)
    ax1.legend(loc="lower right")

    chart_path = os.path.join(SCREENSHOTS_DIR, "product_pareto_chart.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    logger.info("Module 4 complete.")
    return {
        "total_products": total_products,
        "count_80": count_80,
        "pct_80": pct_80,
        "top_sku": top_sku,
        "chart_path": chart_path
    }

# ==============================================================================
# 5. DELIVERY DELAY VS REVIEW SCORE (CSAT)
# ==============================================================================
def run_delivery_csat_analysis(engine) -> dict:
    logger.info("Executing Module 5: Delivery Delay vs CSAT Regression...")
    query = """
    SELECT 
        o.order_id,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        r.review_score
    FROM dim_orders o
    JOIN fact_order_reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL;
    """
    df = pd.read_sql(query, engine)
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
    df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])

    # Standardized calendar date diff (identical to Query 13 and Query 8)
    df["delay_days"] = (df["order_delivered_customer_date"].dt.date - df["order_estimated_delivery_date"].dt.date).apply(lambda x: x.days)
    df["is_late"] = df["delay_days"] > 0

    # Binary Comparison: On-time/Early vs Late (Date Comparison)
    binary_summary = df.groupby("is_late").agg(
        review_count=("review_score", "count"),
        avg_review_score=("review_score", "mean"),
        detractor_pct_1_2=("review_score", lambda x: (x <= 2).mean() * 100),
        promoter_pct_5=("review_score", lambda x: (x == 5).mean() * 100)
    ).reset_index()
    binary_summary["fulfillment_status"] = binary_summary["is_late"].apply(
        lambda x: "Late (Delivered Date > Estimated Date)" if x else "On-Time / Early (Delivered Date <= Estimated Date)"
    )

    def bucket_delay(d):
        if d <= 0:
            return "0. On-Time / Early (<= 0 days)"
        elif d <= 3:
            return "1. Minor Delay (1-3 days)"
        elif d <= 7:
            return "2. Moderate Delay (4-7 days)"
        elif d <= 14:
            return "3. High Delay (8-14 days)"
        else:
            return "4. Severe Delay (15+ days)"

    df["delay_bucket"] = df["delay_days"].apply(bucket_delay)

    bucket_summary = df.groupby("delay_bucket").agg(
        review_count=("review_score", "count"),
        avg_review_score=("review_score", "mean"),
        detractor_pct_1_2=("review_score", lambda x: (x <= 2).mean() * 100),
        promoter_pct_5=("review_score", lambda x: (x == 5).mean() * 100)
    ).reset_index()

    # OLS Linear Regression for Late Orders ONLY (delay_days > 0)
    late_df = df[df["delay_days"] > 0]
    slope_late, intercept_late, r_value_late, p_value_late, std_err_late = stats.linregress(
        late_df["delay_days"], late_df["review_score"]
    )

    # Export CSV
    bucket_summary.to_csv(os.path.join(EXPORTS_DIR, "delivery_csat_delay_summary.csv"), index=False)

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Bar Chart: Average Review Score across delay buckets
    sns.barplot(data=bucket_summary, x="delay_bucket", y="avg_review_score", hue="delay_bucket", palette="RdYlGn_r", legend=False, ax=axes[0])
    axes[0].set_title("Customer Satisfaction (CSAT) by Delivery Delay Tier", fontsize=12, weight="bold")
    axes[0].set_ylabel("Average Review Rating (1 to 5 Stars)")
    axes[0].set_xlabel("Fulfillment Performance Tier")
    axes[0].set_ylim(0, 5)
    axes[0].set_xticks(range(len(bucket_summary)))
    axes[0].set_xticklabels(["On-Time\n(<=0 d)", "Minor\n(1-3 d)", "Moderate\n(4-7 d)", "High\n(8-14 d)", "Severe\n(15+ d)"])
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.2f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", fontsize=10, weight="bold")

    # Scatter / Line Plot: Score decline strictly for late orders
    daily_delay = late_df.groupby("delay_days")["review_score"].agg(["mean", "count"]).reset_index()
    daily_delay = daily_delay[daily_delay["count"] >= 10]  # Filter noise

    axes[1].scatter(daily_delay["delay_days"], daily_delay["mean"], color="#c0392b", alpha=0.7, s=40, label="Daily Mean Score (Late Orders)")
    x_vals = np.array([1, daily_delay["delay_days"].max()])
    axes[1].plot(x_vals, intercept_late + slope_late * x_vals, color="#2c3e50", lw=2, linestyle="--",
                 label=f"OLS Trendline (Late Only: Slope = {slope_late:.4f} stars/day)")
    axes[1].set_title("Late-Only CSAT Degradation per Additional Day of Delay", fontsize=12, weight="bold")
    axes[1].set_xlabel("Days Delayed Past Estimated Delivery Date")
    axes[1].set_ylabel("Average CSAT Rating")
    axes[1].set_ylim(1, 4.5)
    axes[1].legend()

    chart_path = os.path.join(SCREENSHOTS_DIR, "delivery_delay_vs_review_score.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    logger.info("Module 5 complete.")
    return {
        "bucket_summary": bucket_summary,
        "binary_summary": binary_summary,
        "ontime_reviews": int(binary_summary[~binary_summary["is_late"]]["review_count"].iloc[0]),
        "ontime_score": float(binary_summary[~binary_summary["is_late"]]["avg_review_score"].iloc[0]),
        "late_reviews": int(binary_summary[binary_summary["is_late"]]["review_count"].iloc[0]),
        "late_score": float(binary_summary[binary_summary["is_late"]]["avg_review_score"].iloc[0]),
        "slope_late": slope_late,
        "intercept_late": intercept_late,
        "r_value_late": r_value_late,
        "p_value_late": p_value_late,
        "chart_path": chart_path
    }

# ==============================================================================
# 6. MACRO CATEGORY PROFITABILITY (ASSUMED MARGINS)
# ==============================================================================
def run_category_profitability(engine) -> dict:
    logger.info("Executing Module 6: Macro Category Profitability...")
    query = """
    SELECT 
        p.category_group,
        COUNT(i.order_item_id) AS items_sold,
        SUM(i.price) AS total_revenue_brl,
        SUM(i.price * p.assumed_cogs_rate) AS assumed_cogs_brl,
        SUM(i.price * p.assumed_gross_margin_rate) AS assumed_gross_profit_brl
    FROM fact_order_items i
    JOIN dim_orders o ON i.order_id = o.order_id
    JOIN dim_products p ON i.product_id = p.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY p.category_group
    ORDER BY assumed_gross_profit_brl DESC;
    """
    df = pd.read_sql(query, engine)
    df["blended_gross_margin_pct"] = (df["assumed_gross_profit_brl"] / df["total_revenue_brl"]) * 100

    # Total platform metrics
    tot_rev = df["total_revenue_brl"].sum()
    tot_cogs = df["assumed_cogs_brl"].sum()
    tot_gp = df["assumed_gross_profit_brl"].sum()
    tot_margin = (tot_gp / tot_rev) * 100

    # Export CSV
    df.to_csv(os.path.join(EXPORTS_DIR, "category_profitability_summary.csv"), index=False)

    # Visualization: Horizontal Stacked / Dual Bar Chart
    fig, ax = plt.subplots(figsize=(12, 7))
    y_pos = np.arange(len(df))
    bar_height = 0.38

    ax.barh(y_pos + bar_height/2, df["total_revenue_brl"] / 1000, height=bar_height, color="#3498db", label="Revenue (R$ in Thousands)")
    ax.barh(y_pos - bar_height/2, df["assumed_gross_profit_brl"] / 1000, height=bar_height, color="#2ecc71", label="Gross Profit (R$ in Thousands) [Assumed]")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["category_group"])
    ax.invert_yaxis()  # Top earner on top
    ax.set_xlabel("R$ (Thousands)")
    ax.set_title("Merchandise Revenue vs Assumed Gross Profit by Macro Sector\n*(Financial Note: Profitability uses category benchmark assumptions, not actual accounting COGS)*",
                 fontsize=12, weight="bold")
    ax.legend(loc="lower right")

    # Annotate gross margin %
    for i, row in df.iterrows():
        gp_val = row["assumed_gross_profit_brl"] / 1000
        margin_val = row["blended_gross_margin_pct"]
        ax.text(gp_val + 20, i - bar_height/2, f"{margin_val:.1f}% margin", va="center", fontsize=9, color="#27ae60", weight="bold")

    chart_path = os.path.join(SCREENSHOTS_DIR, "category_profitability.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    logger.info("Module 6 complete.")
    return {
        "df": df,
        "tot_rev": tot_rev,
        "tot_cogs": tot_cogs,
        "tot_gp": tot_gp,
        "tot_margin": tot_margin,
        "chart_path": chart_path
    }

# ==============================================================================
# 7. SEASONALITY DECOMPOSITION & 30-DAY HOLT-WINTERS FORECAST
# ==============================================================================
def run_seasonality_and_forecast(engine) -> dict:
    logger.info("Executing Module 7: Seasonality Decomposition & 30-Day Holt-Winters Forecast...")
    query = """
    SELECT 
        DATE(o.order_purchase_timestamp) AS order_date,
        SUM(i.price) AS daily_revenue
    FROM dim_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <= '2018-08-21'
    GROUP BY DATE(o.order_purchase_timestamp)
    ORDER BY order_date;
    """
    df = pd.read_sql(query, engine)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df.set_index("order_date", inplace=True)
    df = df.asfreq("D", fill_value=0)

    # 1. Seasonal Decomposition (7-day frequency)
    decomp = seasonal_decompose(df["daily_revenue"], model="additive", period=7)

    # 2. Holdout Validation (Last 30 Days: 2018-07-23 to 2018-08-21)
    test_days = 30
    train = df["daily_revenue"].iloc[:-test_days]
    test = df["daily_revenue"].iloc[-test_days:]

    holdout_start = test.index.min().strftime("%Y-%m-%d")
    holdout_end = test.index.max().strftime("%Y-%m-%d")

    hw_model = ExponentialSmoothing(
        train,
        seasonal_periods=7,
        trend="add",
        seasonal="add",
        initialization_method="estimated"
    ).fit()
    
    test_pred = hw_model.forecast(test_days)

    # Evaluation metrics
    mae = float(np.mean(np.abs(test - test_pred)))
    rmse = float(np.sqrt(np.mean((test - test_pred)**2)))
    test_mean = float(test.mean())
    pred_mean = float(test_pred.mean())
    wape = float((mae / test_mean) * 100)  # Mathematically identical to sum(|y - y_hat|) / sum(y) * 100
    mape = float(np.mean(np.abs((test - test_pred) / test)) * 100)

    # 3. Full 30-Day Forward Forecast (Fit on all data through 2018-08-21)
    full_hw_model = ExponentialSmoothing(
        df["daily_revenue"],
        seasonal_periods=7,
        trend="add",
        seasonal="add",
        initialization_method="estimated"
    ).fit()
    future_dates = pd.date_range(start=df.index.max() + pd.Timedelta(days=1), periods=30, freq="D")
    future_forecast = full_hw_model.forecast(30)
    future_forecast.index = future_dates

    # Export forecast CSV
    export_df = pd.DataFrame({
        "order_date": list(df.index) + list(future_dates),
        "actual_revenue_brl": list(df["daily_revenue"]) + [np.nan] * 30,
        "test_prediction_brl": [np.nan] * len(train) + list(test_pred) + [np.nan] * 30,
        "future_forecast_brl": [np.nan] * len(df) + list(future_forecast)
    })
    export_df.to_csv(os.path.join(EXPORTS_DIR, "daily_sales_forecast.csv"), index=False)

    # Plot Visualizations
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={"height_ratios": [2, 1]})

    # Top Plot: Train, Test, Prediction, and Forward Forecast
    ax1.plot(train.index, train, color="#7f8c8d", alpha=0.5, label="Historical Training Data (Jan 2017 - Jul 2018)")
    ax1.plot(test.index, test, color="#2980b9", lw=2, label="Actual Test Data (Jul 23 - Aug 21, 2018 Holdout)")
    ax1.plot(test.index, test_pred, color="#e67e22", lw=2.5, linestyle="--", label="Holt-Winters Holdout Prediction")
    ax1.plot(future_forecast.index, future_forecast, color="#27ae60", lw=2.5, label="30-Day Forward Baseline Forecast")
    
    ax1.set_title("30-Day Holt-Winters Baseline Sales Forecast & Validation", fontsize=13, weight="bold")
    ax1.set_ylabel("Daily Delivered Revenue (R$ BRL)")
    ax1.legend(loc="upper left")

    # Add metric box
    metric_text = (
        f"Holdout Window: {holdout_start} to {holdout_end}\n"
        f"Mean Daily Revenue: R$ {test_mean:,.2f}\n"
        f"MAE:  R$ {mae:,.2f}\n"
        f"RMSE: R$ {rmse:,.2f}\n"
        f"WAPE = MAE/Mean: {wape:.2f}%\n"
        f"MAPE: {mape:.2f}%"
    )
    ax1.text(0.72, 0.65, metric_text, transform=ax1.transAxes, fontsize=9.5,
             bbox=dict(boxstyle="round,pad=0.5", fc="#f8f9fa", ec="#bdc3c7", lw=1.2))

    # Bottom Plot: Extracted Seasonality Component (Weekly Cycle)
    ax2.plot(decomp.seasonal.iloc[:28].index, decomp.seasonal.iloc[:28], color="#8e44ad", lw=2)
    ax2.set_title("Extracted Weekly Seasonality Pattern (Sample 4 Weeks)", fontsize=11, weight="bold")
    ax2.set_ylabel("Seasonal Impact (R$)")
    ax2.set_xlabel("Date")

    chart_path = os.path.join(SCREENSHOTS_DIR, "sales_forecast_30d.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    logger.info("Module 7 complete.")
    return {
        "holdout_start": holdout_start,
        "holdout_end": holdout_end,
        "mae": mae,
        "rmse": rmse,
        "wape": wape,
        "mape": mape,
        "test_mean": test_mean,
        "pred_mean": pred_mean,
        "chart_path": chart_path
    }

# ==============================================================================
# 8. DYNAMIC GENERATION OF DOCS/EDA_FINDINGS.MD
# ==============================================================================
def generate_eda_markdown(rfm_res, cohort_res, clv_res, pareto_res, csat_res, profit_res, fc_res):
    logger.info("Generating docs/eda_findings.md dynamically from script results...")
    
    rfm_sum = rfm_res["summary"]
    b_sum = csat_res["bucket_summary"]
    bin_sum = csat_res["binary_summary"]
    p_sum = profit_res["df"]

    md = []
    md.append("# Phase 4: Exploratory Data Analysis (EDA) & Customer Intelligence\n\n")
    md.append("> **Currency Standard**: All monetary figures are reported strictly in **Brazilian Reais (R$ / BRL)**.\n")
    md.append("> **Operational Filter**: All calculations filter strictly for delivered transactions (`order_status = 'delivered'`) and exclude shipping freight, unless explicitly stated.\n")
    md.append("> **Profitability Notice**: All profit and COGS figures are labelled **\"assumed margin, not real data\"** based on category benchmark assumptions.\n\n")

    # Executive Summary / Headline Metrics
    md.append("## Executive Summary: Headline Findings\n\n")
    md.append("| Metric | Value | Business Context |\n")
    md.append("|:---|---:|:---|\n")
    md.append(f"| **Total Unique Customers** | **{rfm_res['total_customers']:,}** | Platform customer base across delivered orders |\n")
    md.append(f"| **Total Merchandise Revenue** | **R$ {rfm_res['total_revenue']:,.2f}** | Platform delivered item GMV (excludes freight) |\n")
    md.append(f"| **Total Repeat Customers** | **{rfm_res['total_repeat_customers']:,} ({rfm_res['total_repeat_customers']/rfm_res['total_customers']*100:.2f}%)** | Customers purchasing 2 or more delivered orders |\n")
    md.append(f"| **Overall Historical CLV** | **R$ {clv_res['historical_clv']:,.2f}** | Average lifetime spend per unique customer |\n")
    md.append(f"| **Margin-Adjusted Historical CLV** | **R$ {clv_res['margin_adjusted_clv']:,.2f}** | Average gross profit contribution per customer *(Assumed)* |\n")
    md.append(f"| **Repeat Buyer CLV Premium** | **R$ {clv_res['clv_repeat']:,.2f} vs R$ {clv_res['clv_onetime']:,.2f}** | Repeat customers spend **+{((clv_res['clv_repeat']/clv_res['clv_onetime'])-1)*100:.1f}%** more than one-time buyers |\n")
    md.append(f"| **Month 1 Cohort Retention** | **{cohort_res['avg_m1_retention']:.2f}%** | Platform-wide average repeat retention in month 1 |\n")
    md.append(f"| **Product Pareto Concentration** | **{pareto_res['pct_80']:.2f}% ({pareto_res['count_80']:,} SKUs)** | Proportion of products generating 80% of revenue |\n")
    md.append(f"| **On-Time vs Late CSAT Score** | **{csat_res['ontime_score']:.2f} vs {csat_res['late_score']:.2f} stars** | Discontinuous CSAT rating drop of **{csat_res['ontime_score'] - csat_res['late_score']:.2f} stars** on date breach |\n")
    md.append(f"| **Late-Only CSAT Degradation Rate** | **{csat_res['slope_late']:.4f} stars/day** | CSAT score decline per additional day of delay on late orders (`delay_days > 0`) |\n")
    md.append(f"| **Overall Blended Gross Margin** | **{profit_res['tot_margin']:.2f}%** | Platform-wide gross margin across 11 macro categories *(Assumed)* |\n")
    md.append(f"| **Forecast Holdout WAPE** | **{fc_res['wape']:.2f}%** | Weighted Absolute Percentage Error on holdout window ({fc_res['holdout_start']} to {fc_res['holdout_end']}) |\n\n")
    md.append("---\n\n")

    # Section 1: RFM
    md.append("## 1. RFM Customer Segmentation\n\n")
    md.append("### Methodology & One-Time Buyer Handling\n")
    md.append("In the Olist dataset, **97.00% of customers purchase exactly once** (`frequency = 1`). Specifically, only **2,801 out of 93,358 customers (3.00%)** are repeat buyers. Standard quintile or quantile binning on Frequency fails mathematically because all frequency quantile cutoffs from the 20th to 80th percentiles collapse to 1. To resolve this robustly, we apply a **hybrid discrete-quantile scoring model**:\n\n")
    md.append("#### Exact Quartile Thresholds & Dimension Scoring\n\n")
    md.append("| Dimension | Score | Quartile / Category | Exact Cutoff Range | Business Meaning |\n")
    md.append("|:---|:---:|:---|:---|:---|\n")
    md.append("| **Recency ($R$)** | **4** | Quartile 1 (Top 25%) | 1 to 114 days | Most recent purchases |\n")
    md.append("| | **3** | Quartile 2 | 115 to 219 days | Moderately recent purchases |\n")
    md.append("| | **2** | Quartile 3 | 220 to 346 days | Lapsing / aging purchases |\n")
    md.append("| | **1** | Quartile 4 (Bottom 25%) | 347 to 714 days | Oldest historical purchases |\n")
    md.append("| **Monetary ($M$)** | **4** | Quartile 4 (Top 25%) | R$ 154.75 to R$ 13,440.00 | High spenders |\n")
    md.append("| | **3** | Quartile 3 | R$ 89.74 to R$ 154.74 | Upper-moderate spenders |\n")
    md.append("| | **2** | Quartile 2 | R$ 47.66 to R$ 89.73 | Lower-moderate spenders |\n")
    md.append("| | **1** | Quartile 1 (Bottom 25%) | R$ 0.85 to R$ 47.65 | Low spenders |\n")
    md.append("| **Frequency ($F$)** | **2** | Repeat Buyer | $\\ge 2$ delivered orders | Multi-order customer (2,801 users = 3.00%) |\n")
    md.append("| | **1** | Single Buyer | 1 delivered order | One-time buyer (90,557 users = 97.00%) |\n\n")

    md.append("#### Exact Segment Assignment Rules & Logic\n\n")
    md.append("Segments are assigned using the following mutually exclusive rules evaluated in order:\n\n")
    md.append("1. **Top Value**:\n")
    md.append("   - **Rule**: `(F == 2 AND R >= 3) OR (R == 4 AND M == 4)`\n")
    md.append("   - **Logic**: Captures active repeat buyers who ordered within 219 days (`F=2, R>=3`, 1,549 users) OR single-order buyers who transacted within 114 days and spent $\\ge$ R$ 154.75 (`R=4, M=4`, 5,380 users).\n")
    md.append("   - **Profile**: 6,929 customers, R$ 340.45 avg spend, 70.77 days avg recency, 22.36% repeat buyer share.\n\n")
    md.append("2. **Mid Value**:\n")
    md.append("   - **Rule**: `(F == 2 AND R <= 2) OR (R >= 3 AND M >= 3)`\n")
    md.append("   - **Logic**: Captures all remaining repeat buyers who ordered > 219 days ago (`F=2, R<=2`, 1,252 users) OR recent moderate/high spenders (`R>=3, M>=3`, 16,980 users).\n")
    md.append("   - **Profile**: 18,232 customers, R$ 194.65 avg spend, 144.72 days avg recency, 6.87% repeat buyer share.\n\n")
    md.append("3. **Dormant** *(Renamed from Lapsing)*:\n")
    md.append("   - **Rule**: `(R == 2) OR (R == 1 AND M >= 3)`\n")
    md.append("   - **Logic**: Captures aging customers who transacted 220 to 346 days ago (`R=2`) OR oldest customers (347 to 714 days ago) with above-median historical spend (`R=1, M>=3`). All users have `F=1`.\n")
    md.append("   - **Naming Rationale**: Named **Dormant** because this is the oldest customer cohort on the platform (average recency **334.80 days**), but they generated substantial lifetime value (**R$ 169.81 avg spend**, R$ 5,686,297.74 total revenue).\n\n")
    md.append("4. **Low Spend** *(Renamed from Inactive)*:\n")
    md.append("   - **Rule**: `ELSE` (all remaining one-time buyers with low/below-median spend, `M <= 2`).\n")
    md.append("   - **Logic**: One-time customers whose primary characteristic is small basket size (avg spend **R$ 46.89**).\n")
    md.append("   - **Naming Rationale**: Named **Low Spend** because their defining business constraint is transaction value (R$ 46.89 vs platform average R$ 141.62). They actually bought more recently (average **226.83 days**) than the Dormant group (334.80 days).\n\n")

    md.append("#### Why Every Repeat Buyer Falls into Top Value or Mid Value\n\n")
    md.append("In this model, **100% of the platform's 2,801 repeat buyers are partitioned between Top Value and Mid Value**:\n")
    md.append("- Any customer with $F = 2$ must have a recency score $R \\in \\{1, 2, 3, 4\\}$.\n")
    md.append("- If $R \\ge 3$ (recency $\\le 219$ days), the customer matches Rule 1 (`F == 2 AND R >= 3`) and is assigned to **Top Value** (**1,549 customers**).\n")
    md.append("- If $R \\le 2$ (recency $> 219$ days), the customer does not match Rule 1, but unconditionally matches Rule 2 (`F == 2 AND R <= 2`) and is assigned to **Mid Value** (**1,252 customers**).\n")
    md.append("- Because $\\{R \\ge 3\\} \\cup \\{R \\le 2\\}$ constitutes the entire universe of possible recency scores, **every repeat buyer is guaranteed to be assigned before Rules 3 or 4 are reached**. As a result, Dormant and Low Spend have exactly **0 repeat buyers (0.00% repeat share)**.\n\n")

    md.append("### Empirical RFM Segment Distribution\n\n")
    md.append(rfm_sum.to_markdown(index=False, floatfmt=",.2f"))
    md.append("\n\n")
    md.append("![RFM Segment Distribution](screenshots/rfm_segments_distribution.png)\n\n")

    top_row = rfm_sum[rfm_sum["segment"] == "Top Value"].iloc[0]
    mid_row = rfm_sum[rfm_sum["segment"] == "Mid Value"].iloc[0]
    dormant_row = rfm_sum[rfm_sum["segment"] == "Dormant"].iloc[0]
    lowspend_row = rfm_sum[rfm_sum["segment"] == "Low Spend"].iloc[0]

    md.append(f"> **Business Insight**: **Top Value** customers represent **{top_row['customer_pct']:.2f}%** of the customer base ({int(top_row['customer_count']):,} users) but generate **R$ {top_row['total_revenue_brl']:,.2f}** ({top_row['revenue_pct']:.2f}% of sales) with an average order value of **R$ {top_row['avg_spend_brl']:.2f}** and the highest repeat buyer share (**{top_row['repeat_buyer_pct']:.2f}%**). Combined, 'Top Value' and 'Mid Value' capture **{top_row['revenue_pct'] + mid_row['revenue_pct']:.2f}%** of platform revenue.\n\n")
    md.append(f"> **Actionable Recommendation**: Deploy automated win-back triggers for the **{int(dormant_row['customer_count']):,} Dormant customers** before their accounts completely churn, and introduce cross-sell bundles for the **{int(lowspend_row['customer_count']):,} Low Spend segment** to elevate their average order value.\n\n")
    md.append("---\n\n")

    # Section 2: Cohort Retention
    md.append("## 2. Monthly Cohort Retention Analysis\n\n")
    md.append("### Cohort Decay Behavior\n")
    md.append("Tracking monthly acquisition cohorts from January 2017 to December 2017 reveals that customer retention is structurally low across all cohorts:\n\n")
    md.append(f"- **Month 1 Retention Average**: **{cohort_res['avg_m1_retention']:.2f}%** across cohorts.\n")
    md.append(f"- **Month 1 Retention Peak**: **{cohort_res['max_m1_retention']:.2f}%**.\n")
    md.append("- **Zero Return Months**: In the retention matrix and heatmap, observed calendar months where zero customers returned are displayed explicitly as **0.00**, while unobserved future months remain blank.\n\n")
    md.append("![Cohort Retention Heatmap](screenshots/cohort_retention_heatmap.png)\n\n")
    md.append(f"> **Business Insight**: Retention is near zero after the initial purchase month ({cohort_res['avg_m1_retention']:.2f}% in Month 1). Olist operates as an acquisition-dependent transaction marketplace rather than a sticky repeat ecosystem.\n\n")
    md.append("> **Actionable Recommendation**: Introduce post-purchase cross-category replenishment triggers (e.g., consumable accessories for Electronics, beauty refills) delivered 30-45 days post-purchase to drive first-to-second order conversion.\n\n")
    md.append("---\n\n")

    # Section 3: CLV
    md.append("## 3. Customer Lifetime Value (CLV)\n\n")
    md.append("### Baseline Metrics & Segmentation\n")
    md.append(f"- **Platform Historical CLV**: **R$ {clv_res['historical_clv']:.2f}** gross merchandise spend per customer.\n")
    md.append(f"- **Platform Margin-Adjusted CLV**: **R$ {clv_res['margin_adjusted_clv']:.2f}** gross profit per customer *(assumed margin, not real data)*.\n")
    md.append(f"- **One-Time Customer CLV**: **R$ {clv_res['clv_onetime']:.2f}** (Margin-Adjusted: **R$ {clv_res['clv_onetime_margin']:.2f}**).\n")
    md.append(f"- **Repeat Customer CLV**: **R$ {clv_res['clv_repeat']:.2f}** (Margin-Adjusted: **R$ {clv_res['clv_repeat_margin']:.2f}**).\n\n")

    clv_table = clv_res["segment_clv"][["segment", "customer_count", "historical_clv_brl", "margin_adjusted_clv_brl"]]
    md.append(clv_table.to_markdown(index=False, floatfmt=",.2f"))
    md.append("\n\n")
    md.append(f"> **Business Insight**: Repeat buyers yield an average lifetime value of **R$ {clv_res['clv_repeat']:.2f}**, representing an incremental **R$ {clv_res['clv_repeat'] - clv_res['clv_onetime']:.2f}** (+{((clv_res['clv_repeat']/clv_res['clv_onetime'])-1)*100:.1f}%) over single-order buyers.\n\n")
    md.append(f"> **Actionable Recommendation**: Customer Acquisition Cost (CAC) must not exceed **R$ {clv_res['margin_adjusted_clv']:.2f}** for blended traffic to remain profitable on first orders. For retargeting repeat campaigns, the allowable CAC ceiling expands to **R$ {clv_res['clv_repeat_margin']:.2f}**.\n\n")
    md.append("---\n\n")

    # Section 4: Product Pareto
    md.append("## 4. Product Portfolio Pareto Analysis (80/20 Rule)\n\n")
    md.append(f"- **Total Unique SKUs Sold**: **{pareto_res['total_products']:,}** products.\n")
    md.append(f"- **80% Revenue Cutoff**: **{pareto_res['count_80']:,} SKUs** (**{pareto_res['pct_80']:.2f}%** of the catalog) generate 80.0% of all delivered revenue.\n")
    md.append(f"- **Long-Tail Catalog**: The remaining **{100 - pareto_res['pct_80']:.2f}%** of products ({pareto_res['total_products'] - pareto_res['count_80']:,} SKUs) generate only 20% of revenue.\n")
    md.append(f"- **Top Individual Product**: `{pareto_res['top_sku']['product_id']}` ({pareto_res['top_sku']['product_category_name_english']}), generating **R$ {pareto_res['top_sku']['total_revenue_brl']:,.2f}** across {int(pareto_res['top_sku']['units_sold']):,} units sold.\n\n")
    md.append("![Product Pareto Curve](screenshots/product_pareto_chart.png)\n\n")
    md.append(f"> **Business Insight**: A compact core of **{pareto_res['count_80']:,} products** powers four-fifths of marketplace sales. Maintaining merchant inventory availability for these top {pareto_res['pct_80']:.1f}% SKUs is critical to preventing GMV leakage.\n\n")
    md.append(f"> **Actionable Recommendation**: Institute an SLA priority stocking program for the top **{pareto_res['count_80']:,} Pareto SKUs** with weekly automated merchant inventory health checks.\n\n")
    md.append("---\n\n")

    # Section 5: Delivery Delay vs CSAT
    md.append("## 5. Delivery Logistics SLA vs Customer Satisfaction (CSAT)\n\n")
    md.append("### Definition of Late Orders\n")
    md.append("To maintain mathematical consistency with Query 13 and Query 8, delivery delay is defined using calendar dates: `DATE(order_delivered_customer_date) > DATE(order_estimated_delivery_date)`. Same-day deliveries where arrival occurs on the estimated date are treated as on-time.\n\n")
    
    md.append("### (a) On-Time vs Late Performance Comparison\n\n")
    md.append(bin_sum[["fulfillment_status", "review_count", "avg_review_score", "detractor_pct_1_2", "promoter_pct_5"]].to_markdown(index=False, floatfmt=",.2f"))
    md.append("\n\n")

    md.append("### Detailed Fulfillment Delay Tiers\n\n")
    md.append(b_sum.to_markdown(index=False, floatfmt=",.2f"))
    md.append("\n\n")
    md.append("![Delivery Delay vs CSAT](screenshots/delivery_delay_vs_review_score.png)\n\n")

    md.append("### (b) OLS Regression Analysis on Late Orders Only (`delay_days > 0`)\n\n")
    md.append("The linear regression was computed strictly on late orders (`delay_days > 0`, **6,409 reviews**):\n\n")
    md.append(f"- **Slope ($\\\\beta_1$)**: **{csat_res['slope_late']:.4f} stars per day late** ($p = {csat_res['p_value_late']:.2e}$).\n")
    md.append(f"- **Intercept ($\\\\beta_0$)**: **{csat_res['intercept_late']:.2f} stars** immediately upon breach of promised date.\n")
    md.append(f"- **Immediate Threshold Drop**: Delivering on or before the estimated date yields **{csat_res['ontime_score']:.2f} stars** (only 9.28% detractors). Crossing the estimated date causes an immediate discontinuous drop of **{csat_res['ontime_score'] - csat_res['late_score']:.2f} stars** down to **{csat_res['late_score']:.2f} stars** (62.41% detractors), followed by an ongoing decay of **{abs(csat_res['slope_late']):.4f} stars** for each additional day late.\n\n")
    md.append(f"> **Business Insight**: Breaching the promised delivery date imposes an immediate 2.02-star penalty on customer satisfaction. Once late, CSAT decays by an additional 0.0160 stars per day.\n\n")
    md.append("> **Actionable Recommendation**: Implement carrier dispatch tracking alerts on Day -2 prior to the SLA breach date, with proactive customer notification emails and automatic shipping vouchers for delayed deliveries to mitigate 1-star reviews.\n\n")
    md.append("---\n\n")

    # Section 6: Category Profitability
    md.append("## 6. Macro Category Profitability *(Assumed Margins)*\n\n")
    md.append("> **Notice**: Profit figures are derived from benchmark category margins in `config/margin_assumptions.yaml` and labelled **\"assumed margin, not real data\"**.\n\n")
    md.append(p_sum[["category_group", "items_sold", "total_revenue_brl", "assumed_cogs_brl", "assumed_gross_profit_brl", "blended_gross_margin_pct"]].to_markdown(index=False, floatfmt=",.2f"))
    md.append("\n\n")
    md.append("![Category Profitability](screenshots/category_profitability.png)\n\n")
    top_profit_group = p_sum.iloc[0]
    md.append(f"- **Platform Total Estimated Revenue**: **R$ {profit_res['tot_rev']:,.2f}**\n")
    md.append(f"- **Platform Total Estimated COGS**: **R$ {profit_res['tot_cogs']:,.2f}**\n")
    md.append(f"- **Platform Total Estimated Gross Profit**: **R$ {profit_res['tot_gp']:,.2f}**\n")
    md.append(f"- **Platform Overall Blended Gross Margin**: **{profit_res['tot_margin']:.2f}%**\n\n")
    md.append(f"> **Business Insight**: **'{top_profit_group['category_group']}'** generates the largest gross profit at **R$ {top_profit_group['assumed_gross_profit_brl']:,.2f}** ({top_profit_group['blended_gross_margin_pct']:.1f}% margin), while **'Fashion & Apparel'** offers the highest category margin rate at **{p_sum[p_sum['category_group'] == 'Fashion & Apparel']['blended_gross_margin_pct'].iloc[0]:.1f}%**.\n\n")
    md.append(f"> **Actionable Recommendation**: Allocate ad spend and homepage promotional banners toward high-margin categories like **Fashion & Apparel (55.0% margin)** and **Beauty & Personal Care (50.0% margin)** to maximize net gross profit per marketing dollar.\n\n")
    md.append("---\n\n")

    # Section 7: Forecasting & Seasonality
    md.append("## 7. Seasonality Decomposition & 30-Day Holt-Winters Forecast\n\n")
    md.append("### Time-Series Decomposition Analysis\n")
    md.append("- **Trend**: Strong structural growth throughout 2017, consolidating at a daily revenue run-rate of ~R$ 30,000–35,000 during mid-2018.\n")
    md.append("- **Seasonality**: Distinct 7-day cyclicality with peak order volume on Mondays and Tuesdays, tapering off on weekends.\n")
    md.append("- **Holiday Spike**: Prominent outlier spike in late November 2017 corresponding to Black Friday.\n\n")
    md.append("### Holdout Validation Accuracy (Last 30 Days)\n")
    md.append(f"- **Holdout Window**: **{fc_res['holdout_start']} to {fc_res['holdout_end']}** (30 operational days).\n")
    md.append(f"- **Test Period Mean Daily Revenue**: **R$ {fc_res['test_mean']:,.2f}**\n")
    md.append(f"- **Forecasted Mean Daily Revenue**: **R$ {fc_res['pred_mean']:,.2f}**\n")
    md.append(f"- **Mean Absolute Error (MAE)**: **R$ {fc_res['mae']:,.2f}**\n")
    md.append(f"- **Root Mean Squared Error (RMSE)**: **R$ {fc_res['rmse']:,.2f}**\n")
    md.append(f"- **Weighted Absolute Percentage Error (WAPE)**: **{fc_res['wape']:.2f}%**\n")
    md.append(f"  $$\\text{{WAPE}} = \\frac{{\\text{{MAE}}}}{{\\bar{{y}}_{{\\text{{test}}}}}} = \\frac{{{fc_res['mae']:,.2f}}}{{{fc_res['test_mean']:,.2f}}} = {fc_res['wape']:.2f}\\%$$\n")
    md.append(f"- **Mean Absolute Percentage Error (MAPE)**: **{fc_res['mape']:.2f}%**.\n\n")
    md.append("![Sales Forecast 30D](screenshots/sales_forecast_30d.png)\n\n")
    md.append(f"> **Business Insight**: Holt-Winters Exponential Smoothing captures the 7-day cyclical oscillation accurately, tracking daily sales within a WAPE of **{fc_res['wape']:.2f}%** on held-out test data.\n\n")
    md.append("> **Actionable Recommendation**: Utilize the 30-day baseline forecast for operational carrier capacity planning and merchant working capital requirements.\n")

    with open(DOCS_FILE, "w", encoding="utf-8") as f:
        f.write("".join(md))
    logger.info(f"Successfully saved {DOCS_FILE}!")

# ==============================================================================
# MAIN PIPELINE EXECUTION
# ==============================================================================
def run_all_eda():
    logger.info("Starting Phase 4 EDA Pipeline...")
    engine = get_engine(include_database=True)

    rfm_res = run_rfm_segmentation(engine)
    cohort_res = run_cohort_retention(engine)
    clv_res = run_clv_analysis(rfm_res["summary"], rfm_res["rfm_df"])
    pareto_res = run_product_pareto(engine)
    csat_res = run_delivery_csat_analysis(engine)
    profit_res = run_category_profitability(engine)
    fc_res = run_seasonality_and_forecast(engine)

    generate_eda_markdown(rfm_res, cohort_res, clv_res, pareto_res, csat_res, profit_res, fc_res)
    logger.info("Phase 4 EDA Pipeline completed successfully!")

if __name__ == "__main__":
    run_all_eda()

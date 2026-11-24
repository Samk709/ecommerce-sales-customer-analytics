# Phase 4: Exploratory Data Analysis (EDA) & Customer Intelligence

> **Currency Standard**: All monetary figures are reported strictly in **Brazilian Reais (R$ / BRL)**.
> **Operational Filter**: All calculations filter strictly for delivered transactions (`order_status = 'delivered'`) and exclude shipping freight, unless explicitly stated.
> **Profitability Notice**: All profit and COGS figures are labelled **"assumed margin, not real data"** based on category benchmark assumptions.

## Executive Summary: Headline Findings

| Metric | Value | Business Context |
|:---|---:|:---|
| **Total Unique Customers** | **93,358** | Platform customer base across delivered orders |
| **Total Merchandise Revenue** | **R$ 13,221,498.11** | Platform delivered item GMV (excludes freight) |
| **Total Repeat Customers** | **2,801 (3.00%)** | Customers purchasing 2 or more delivered orders |
| **Overall Historical CLV** | **R$ 141.62** | Average lifetime spend per unique customer |
| **Margin-Adjusted Historical CLV** | **R$ 57.72** | Average gross profit contribution per customer *(Assumed)* |
| **Repeat Buyer CLV Premium** | **R$ 260.05 vs R$ 137.96** | Repeat customers spend **+88.5%** more than one-time buyers |
| **Month 1 Cohort Retention** | **0.49% (2017 heatmap) / 0.47% (18 cohorts)** | Average repeat retention in month 1 (0.49% across 12 heatmap cohorts; 0.47% unweighted across 18 cohorts Jan 2017–Jun 2018; peak 0.72% in Oct 2017) |
| **Product Pareto Concentration** | **25.93% (8,352 SKUs)** | Proportion of products generating 80% of revenue |
| **On-Time vs Late CSAT Score** | **4.29 vs 2.27 stars** | Discontinuous CSAT rating drop of **2.02 stars** on date breach |
| **Late-Only CSAT Degradation Rate** | **-0.0160 stars/day** | CSAT score decline per additional day of delay on late orders (`delay_days > 0`) |
| **Overall Blended Gross Margin** | **40.76%** | Platform-wide gross margin across 11 macro categories *(Assumed)* |
| **Forecast Holdout WAPE** | **12.90%** | Weighted Absolute Percentage Error on holdout window (2018-07-22 to 2018-08-20) |

---

## 1. RFM Customer Segmentation

### Methodology & One-Time Buyer Handling
In the Olist dataset, **97.00% of customers purchase exactly once** (`frequency = 1`). Specifically, only **2,801 out of 93,358 customers (3.00%)** are repeat buyers. Standard quintile or quantile binning on Frequency fails mathematically because all frequency quantile cutoffs from the 20th to 80th percentiles collapse to 1. To resolve this robustly, we apply a **hybrid discrete-quantile scoring model**:

#### Exact Quartile Thresholds & Dimension Scoring

| Dimension | Score | Quartile / Category | Exact Cutoff Range | Business Meaning |
|:---|:---:|:---|:---|:---|
| **Recency ($R$)** | **4** | Quartile 1 (Top 25%) | 1 to 114 days | Most recent purchases |
| | **3** | Quartile 2 | 115 to 219 days | Moderately recent purchases |
| | **2** | Quartile 3 | 220 to 346 days | Lapsing / aging purchases |
| | **1** | Quartile 4 (Bottom 25%) | 347 to 714 days | Oldest historical purchases |
| **Monetary ($M$)** | **4** | Quartile 4 (Top 25%) | R$ 154.75 to R$ 13,440.00 | High spenders |
| | **3** | Quartile 3 | R$ 89.74 to R$ 154.74 | Upper-moderate spenders |
| | **2** | Quartile 2 | R$ 47.66 to R$ 89.73 | Lower-moderate spenders |
| | **1** | Quartile 1 (Bottom 25%) | R$ 0.85 to R$ 47.65 | Low spenders |
| **Frequency ($F$)** | **2** | Repeat Buyer | $\ge 2$ delivered orders | Multi-order customer (2,801 users = 3.00%) |
| | **1** | Single Buyer | 1 delivered order | One-time buyer (90,557 users = 97.00%) |

#### Exact Segment Assignment Rules & Logic

Segments are assigned using the following mutually exclusive rules evaluated in order:

1. **Top Value**:
   - **Rule**: `(F == 2 AND R >= 3) OR (R == 4 AND M == 4)`
   - **Logic**: Captures active repeat buyers who ordered within 219 days (`F=2, R>=3`, 1,549 users) OR single-order buyers who transacted within 114 days and spent $\ge$ R$ 154.75 (`R=4, M=4`, 5,380 users).
   - **Profile**: 6,929 customers, R$ 340.45 avg spend, 70.77 days avg recency, 22.36% repeat buyer share.

2. **Mid Value**:
   - **Rule**: `(F == 2 AND R <= 2) OR (R >= 3 AND M >= 3)`
   - **Logic**: Captures all remaining repeat buyers who ordered > 219 days ago (`F=2, R<=2`, 1,252 users) OR recent moderate/high spenders (`R>=3, M>=3`, 16,980 users).
   - **Profile**: 18,232 customers, R$ 194.65 avg spend, 144.72 days avg recency, 6.87% repeat buyer share.

3. **Dormant** *(Renamed from Lapsing)*:
   - **Rule**: `(R == 2) OR (R == 1 AND M >= 3)`
   - **Logic**: Captures aging customers who transacted 220 to 346 days ago (`R=2`) OR oldest customers (347 to 714 days ago) with above-median historical spend (`R=1, M>=3`). All users have `F=1`.
   - **Naming Rationale**: Named **Dormant** because this is the oldest customer cohort on the platform (average recency **334.80 days**), but they generated substantial lifetime value (**R$ 169.81 avg spend**, R$ 5,686,297.74 total revenue).

4. **Low Spend** *(Renamed from Inactive)*:
   - **Rule**: `ELSE` (all remaining one-time buyers with low/below-median spend, `M <= 2`).
   - **Logic**: One-time customers whose primary characteristic is small basket size (avg spend **R$ 46.89**).
   - **Naming Rationale**: Named **Low Spend** because their defining business constraint is transaction value (R$ 46.89 vs platform average R$ 141.62). They actually bought more recently (average **226.83 days**) than the Dormant group (334.80 days).

#### Why Every Repeat Buyer Falls into Top Value or Mid Value

In this model, **100% of the platform's 2,801 repeat buyers are partitioned between Top Value and Mid Value**:
- Any customer with $F = 2$ must have a recency score $R \in \{1, 2, 3, 4\}$.
- If $R \ge 3$ (recency $\le 219$ days), the customer matches Rule 1 (`F == 2 AND R >= 3`) and is assigned to **Top Value** (**1,549 customers**).
- If $R \le 2$ (recency $> 219$ days), the customer does not match Rule 1, but unconditionally matches Rule 2 (`F == 2 AND R <= 2`) and is assigned to **Mid Value** (**1,252 customers**).
- Because $\{R \ge 3\} \cup \{R \le 2\}$ constitutes the entire universe of possible recency scores, **every repeat buyer is guaranteed to be assigned before Rules 3 or 4 are reached**. As a result, Dormant and Low Spend have exactly **0 repeat buyers (0.00% repeat share)**.

### Empirical RFM Segment Distribution

| segment   |   customer_count |   customer_pct |   repeat_customers |   repeat_buyer_pct |   total_revenue_brl |   revenue_pct |   avg_recency_days |   avg_frequency |   avg_spend_brl |
|:----------|-----------------:|---------------:|-------------------:|-------------------:|--------------------:|--------------:|-------------------:|----------------:|----------------:|
| Top Value |             6929 |           7.42 |               1549 |              22.36 |        2,358,970.15 |         17.84 |              70.77 |            1.26 |          340.45 |
| Mid Value |            18232 |          19.53 |               1252 |               6.87 |        3,548,822.05 |         26.84 |             144.72 |            1.07 |          194.65 |
| Dormant   |            33487 |          35.87 |                  0 |               0.00 |        5,686,297.74 |         43.01 |             334.80 |            1.00 |          169.81 |
| Low Spend |            34710 |          37.18 |                  0 |               0.00 |        1,627,408.17 |         12.31 |             226.83 |            1.00 |           46.89 |

![RFM Segment Distribution](screenshots/rfm_segments_distribution.png)

> **Business Insight**: **Top Value** customers represent **7.42%** of the customer base (6,929 users) but generate **R$ 2,358,970.15** (17.84% of sales) with an average order value of **R$ 340.45** and the highest repeat buyer share (**22.36%**). Combined, 'Top Value' and 'Mid Value' capture **44.68%** of platform revenue.

> **Actionable Recommendation**: Deploy automated win-back triggers for the **33,487 Dormant customers** before their accounts completely churn, and introduce cross-sell bundles for the **34,710 Low Spend segment** to elevate their average order value.

---

## 2. Monthly Cohort Retention Analysis

### Cohort Decay Behavior
Tracking monthly acquisition cohorts from January 2017 to December 2017 reveals that customer retention is structurally low across all cohorts:

- **Month 1 Retention Average (2017 Heatmap Cohorts)**: **0.49%** (simple unweighted average across the 12 displayed 2017 monthly cohorts: Jan 2017 to Dec 2017).
- **Month 1 Retention Average (18 Observed Cohorts)**: **0.47%** (simple unweighted average across all 18 cohorts from Jan 2017 to Jun 2018 having $\ge 1$ month observable repurchase follow-up).
- **Month 1 Retention Peak**: **0.72%** (achieved by the **October 2017 cohort**; the March 2017 cohort recorded **0.44%**).
- **Zero Return Months**: In the retention matrix and heatmap, observed calendar months where zero customers returned are displayed explicitly as **0.00**, while unobserved future months remain blank.

![Cohort Retention Heatmap](screenshots/cohort_retention_heatmap.png)

> **Business Insight**: Retention is near zero after the initial purchase month (0.49% average across 2017 cohorts, 0.47% across 18 cohorts). Olist operates as an acquisition-dependent transaction marketplace rather than a sticky repeat ecosystem.

> **Actionable Recommendation**: Introduce post-purchase cross-category replenishment triggers (e.g., consumable accessories for Electronics, beauty refills) delivered 30-45 days post-purchase to drive first-to-second order conversion.

---

## 3. Customer Lifetime Value (CLV)

### Baseline Metrics & Segmentation
- **Platform Historical CLV**: **R$ 141.62** gross merchandise spend per customer.
- **Platform Margin-Adjusted CLV**: **R$ 57.72** gross profit per customer *(assumed margin, not real data)*.
- **One-Time Customer CLV**: **R$ 137.96** (Margin-Adjusted: **R$ 56.23**).
- **Repeat Customer CLV**: **R$ 260.05** (Margin-Adjusted: **R$ 106.00**).

| segment   |   customer_count |   historical_clv_brl |   margin_adjusted_clv_brl |
|:----------|-----------------:|---------------------:|--------------------------:|
| Top Value |             6929 |               340.45 |                    138.77 |
| Mid Value |            18232 |               194.65 |                     79.34 |
| Dormant   |            33487 |               169.81 |                     69.21 |
| Low Spend |            34710 |                46.89 |                     19.11 |

> **Business Insight**: Repeat buyers yield an average lifetime value of **R$ 260.05**, representing an incremental **R$ 122.09** (+88.5%) over single-order buyers.

> **Actionable Recommendation**: Customer Acquisition Cost (CAC) must not exceed **R$ 57.72** for blended traffic to remain profitable on first orders. For retargeting repeat campaigns, the allowable CAC ceiling expands to **R$ 106.00**.

---

## 4. Product Portfolio Pareto Analysis (80/20 Rule)

- **Total Unique SKUs Sold**: **32,216** products.
- **80% Revenue Cutoff**: **8,352 SKUs** (**25.93%** of the catalog) generate 80.0% of all delivered revenue.
- **Long-Tail Catalog**: The remaining **74.07%** of products (23,864 SKUs) generate only 20% of revenue.
- **Top Individual Product**: `bb50f2e236e5eea0100680137654686c` (health_beauty), generating **R$ 63,560.00** across 194 units sold.

![Product Pareto Curve](screenshots/product_pareto_chart.png)

> **Business Insight**: A compact core of **8,352 products** powers four-fifths of marketplace sales. Maintaining merchant inventory availability for these top 25.9% SKUs is critical to preventing GMV leakage.

> **Actionable Recommendation**: Institute an SLA priority stocking program for the top **8,352 Pareto SKUs** with weekly automated merchant inventory health checks.

---

## 5. Delivery Logistics SLA vs Customer Satisfaction (CSAT)

### Definition of Late Orders
To maintain mathematical consistency with Query 13 and Query 8, delivery delay is defined using calendar dates: `DATE(order_delivered_customer_date) > DATE(order_estimated_delivery_date)`. Same-day deliveries where arrival occurs on the estimated date are treated as on-time.

### (a) On-Time vs Late Performance Comparison

| fulfillment_status                                 |   review_count |   avg_review_score |   detractor_pct_1_2 |   promoter_pct_5 |
|:---------------------------------------------------|---------------:|-------------------:|--------------------:|-----------------:|
| On-Time / Early (Delivered Date <= Estimated Date) |          89944 |               4.29 |                9.28 |            62.26 |
| Late (Delivered Date > Estimated Date)             |           6409 |               2.27 |               62.41 |            16.54 |

### Detailed Fulfillment Delay Tiers

| delay_bucket                   |   review_count |   avg_review_score |   detractor_pct_1_2 |   promoter_pct_5 |
|:-------------------------------|---------------:|-------------------:|--------------------:|-----------------:|
| 0. On-Time / Early (<= 0 days) |          89944 |               4.29 |                9.28 |            62.26 |
| 1. Minor Delay (1-3 days)      |           1856 |               3.29 |               32.17 |            33.14 |
| 2. Moderate Delay (4-7 days)   |           1756 |               2.10 |               67.65 |            14.12 |
| 3. High Delay (8-14 days)      |           1452 |               1.68 |               80.03 |             6.96 |
| 4. Severe Delay (15+ days)     |           1345 |               1.72 |               78.29 |             7.14 |

![Delivery Delay vs CSAT](screenshots/delivery_delay_vs_review_score.png)

### (b) OLS Regression Analysis on Late Orders Only (`delay_days > 0`)

The linear regression was computed strictly on late orders (`delay_days > 0`, **6,409 reviews**):

- **Slope ($\\beta_1$)**: **-0.0160 stars per day late** ($p = 3.48e-32$).
- **Intercept ($\\beta_0$)**: **2.44 stars** immediately upon breach of promised date.
- **Immediate Threshold Drop**: Delivering on or before the estimated date yields **4.29 stars** (only 9.28% detractors). Crossing the estimated date causes an immediate discontinuous drop of **2.02 stars** down to **2.27 stars** (62.41% detractors), followed by an ongoing decay of **0.0160 stars** for each additional day late.

> **Business Insight**: Breaching the promised delivery date imposes an immediate 2.02-star penalty on customer satisfaction. Once late, CSAT decays by an additional 0.0160 stars per day.

> **Actionable Recommendation**: Implement carrier dispatch tracking alerts on Day -2 prior to the SLA breach date, with proactive customer notification emails and automatic shipping vouchers for delayed deliveries to mitigate 1-star reviews.

---

## 6. Macro Category Profitability *(Assumed Margins)*

> **Notice**: Profit figures are derived from benchmark category margins in `config/margin_assumptions.yaml` and labelled **"assumed margin, not real data"**.

| category_group          |   items_sold |   total_revenue_brl |   assumed_cogs_brl |   assumed_gross_profit_brl |   blended_gross_margin_pct |
|:------------------------|-------------:|--------------------:|-------------------:|---------------------------:|---------------------------:|
| Furniture & Home Decor  |        28944 |        2,814,172.03 |       1,688,503.22 |               1,125,668.81 |                      40.00 |
| Sports, Toys & Hobbies  |        16545 |        2,055,585.30 |       1,130,571.92 |                 925,013.39 |                      45.00 |
| Fashion & Apparel       |         9511 |        1,502,217.15 |         675,997.72 |                 826,219.43 |                      55.00 |
| Beauty & Personal Care  |        12842 |        1,624,777.16 |         812,388.58 |                 812,388.58 |                      50.00 |
| Commercial & General    |         8154 |        1,151,085.39 |         690,651.23 |                 460,434.16 |                      40.00 |
| Computers & Electronics |        16869 |        1,841,711.92 |       1,381,283.94 |                 460,427.98 |                      25.00 |
| Tools & Construction    |         6599 |          813,741.79 |         528,932.16 |                 284,809.63 |                      35.00 |
| Automotive & Parts      |         4140 |          578,966.65 |         405,276.66 |                 173,689.99 |                      30.00 |
| Home Appliances         |         2033 |          475,442.29 |         309,037.49 |                 166,404.80 |                      35.00 |
| Books & Media           |         3398 |          297,484.52 |         163,616.49 |                 133,868.03 |                      45.00 |
| Food, Drinks & Flowers  |         1162 |           66,313.91 |          46,419.74 |                  19,894.17 |                      30.00 |

![Category Profitability](screenshots/category_profitability.png)

- **Platform Total Estimated Revenue**: **R$ 13,221,498.11**
- **Platform Total Estimated COGS**: **R$ 7,832,679.13**
- **Platform Total Estimated Gross Profit**: **R$ 5,388,818.98**
- **Platform Overall Blended Gross Margin**: **40.76%**

> **Business Insight**: **'Furniture & Home Decor'** generates the largest gross profit at **R$ 1,125,668.81** (40.0% margin), while **'Fashion & Apparel'** offers the highest category margin rate at **55.0%**.

> **Actionable Recommendation**: Allocate ad spend and homepage promotional banners toward high-margin categories like **Fashion & Apparel (55.0% margin)** and **Beauty & Personal Care (50.0% margin)** to maximize net gross profit per marketing dollar.

---

## 7. Seasonality Decomposition & 30-Day Holt-Winters Forecast

### Time-Series Decomposition Analysis
- **Trend**: Strong structural growth throughout 2017, consolidating at a daily revenue run-rate of ~R$ 30,000–35,000 during mid-2018.
- **Seasonality**: Distinct 7-day cyclicality with peak order volume on Mondays and Tuesdays, tapering off on weekends.
- **Holiday Spike**: Prominent outlier spike in late November 2017 corresponding to Black Friday.

### Holdout Validation Accuracy (Last 30 Days)
- **Holdout Window**: **2018-07-22 to 2018-08-20** (30 operational days).
- **Test Period Mean Daily Revenue**: **R$ 36,038.69**
- **Forecasted Mean Daily Revenue**: **R$ 33,741.09**
- **Mean Absolute Error (MAE)**: **R$ 4,647.90**
- **Root Mean Squared Error (RMSE)**: **R$ 5,693.14**
- **Weighted Absolute Percentage Error (WAPE)**: **12.90%**
  $$\text{WAPE} = \frac{\text{MAE}}{\bar{y}_{\text{test}}} = \frac{4,647.90}{36,038.69} = 12.90\%$$
- **Mean Absolute Percentage Error (MAPE)**: **12.36%**.

![Sales Forecast 30D](screenshots/sales_forecast_30d.png)

> **Business Insight**: Holt-Winters Exponential Smoothing captures the 7-day cyclical oscillation accurately, tracking daily sales within a WAPE of **12.90%** on held-out test data.

> **Actionable Recommendation**: Utilize the 30-day baseline forecast for operational carrier capacity planning and merchant working capital requirements.

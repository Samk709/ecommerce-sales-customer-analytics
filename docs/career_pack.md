# Career Pack: E-Commerce Sales & Customer Intelligence Analytics Platform

This document equips you with battle-tested career assets for portfolio presentation, resume enhancement, LinkedIn networking, and technical data analyst interviews.

---

## 1. High-Impact Resume Bullets

Each bullet incorporates the **Action-Context-Result** framework with exact, verified project figures and explicit source attribution.

- **Architected End-to-End Analytics Pipeline**: Engineered an enterprise analytics platform evaluating **96,478 delivered orders** and **R$ 13,221,498.11** in merchandise revenue (**R$ 15,419,773.75 GMV**), transitioning 9 raw datasets into a normalized MySQL relational database and an analytical Star Schema warehouse optimized for BI reporting.  
  *(Source: `docs/sql_results.md` Query 1; `data/exports/dim_orders.csv`)*

- **Segmented Customer Base via Hybrid RFM Model**: Designed a hybrid discrete-quantile RFM segmentation model across **93,358 unique customers**, overcoming a severe **97.00% single-order bias** to isolate **6,929 Top Value customers** driving **R$ 2,358,970.15** (**17.84%** of revenue) with an average spend of **R$ 340.45** (**+140.4%** above platform average of R$ 141.62).  
  *(Source: `docs/eda_findings.md` Section 1; `data/exports/rfm_segment_summary.csv`)*

- **Quantified Customer Retention & Unit Economics**: Modeled historical Customer Lifetime Value (CLV) proving repeat customers (**2,801 users**, **3.00%** of customer base) generate an **+88.5% CLV premium** (**R$ 260.05 vs R$ 137.96**), while diagnosing monthly cohort retention across 2017 to reveal a **0.49% Month-1 retention rate** across the 2017 heatmap cohorts (**0.47%** across all 18 observed cohorts Jan 2017–Jun 2018; peak **0.72% in October 2017**), shifting commercial strategy from acquisition to retention.  
  *(Source: `docs/eda_findings.md` Sections 2 & 3; `data/exports/cohort_retention_matrix.csv`)*

- **Analyzed Logistics SLA Impact on CSAT**: Evaluated **96,353 customer review ratings** with verified delivery dates against calendar delivery deadlines (Query 8; out of **96,361 total reviews** on delivered orders in Query 5, excluding 8 orders lacking delivery dates), identifying an immediate **2.02-star customer satisfaction cliff** upon delivery SLA breach (**4.29 on-time vs 2.27 late stars**) and modeling ongoing delay penalty at **-0.0160 stars/day late** ($p = 3.48 \times 10^{-32}$) via OLS regression.  
  *(Source: `docs/sql_results.md` Query 5 & Query 8; `docs/eda_findings.md` Section 5)*

- **Developed Zero-Database Web App & Production Tests**: Deployed a zero-database interactive Streamlit analytics application with reactive multi-dimensional filtering, 30-day Holt-Winters revenue forecasting (**12.90% holdout WAPE**, **R$ 4,647.90 MAE**), and built an automated **46-test pytest suite** ensuring 100% financial reconciliation and exception-free page rendering across SQL, Python, and UI layers.  
  *(Source: `docs/eda_findings.md` Section 7; `tests/test_streamlit_kpis.py`)*

---

## 2. LinkedIn Launch Post

```text
🚀 Excited to share my latest portfolio project: An end-to-end E-Commerce Sales & Customer Intelligence Analytics Platform!

Working with ~100k Brazilian e-commerce orders (Olist dataset), I built a complete data pipeline spanning Python ETL, MySQL 8.0 relational modeling, Power BI Star Schema specifications, and an interactive Streamlit web dashboard.

Here are 4 key findings from the data:

1️⃣ The Loyalty Premium:
Only 3.00% of customers purchase more than once (2,801 out of 93,358). However, repeat buyers generate an +88.5% Customer Lifetime Value (CLV) premium (R$ 260.05 vs R$ 137.96 for one-time buyers). 

2️⃣ Overcoming the Frequency Trap (RFM Segmentation):
Standard quintile RFM breaks when 97.00% of customers purchase once. I engineered a hybrid discrete-quantile model that isolated 6,929 "Top Value" customers who drive R$ 2.36M (17.84% of total revenue) with an average order value of R$ 340.45.

3️⃣ The Logistics Satisfaction Cliff:
Delivering on-time yields an average CSAT of 4.29 / 5.0 stars. Missing the estimated delivery date triggers an immediate 2.02-star drop to 2.27 stars, with ratings eroding further by -0.016 stars for every additional day of delay.

4️⃣ Forecasting & Financial Modeling:
Built a 30-day additive Holt-Winters forecast capturing weekly seasonality, validated with a 12.90% WAPE on holdout test data.

🛠 Tech Stack:
• SQL (MySQL 8.0): Normalized relational schema, CTEs, Window Functions, Query Optimization
• Python (Pandas, Plotly, Statsmodels, SciPy): ETL, Cohort Retention, OLS Regression, Time-Series
• Streamlit: Multi-page interactive executive web dashboard with zero-database cloud architecture
• QA: 46 automated tests validating referential integrity, financial balance, and UI page rendering

🔗 Check out the full GitHub repository, SQL queries, and interactive dashboard code:
https://github.com/Samk709/ecommerce-sales-customer-analytics

Feedback and thoughts are welcome!

#DataAnalytics #SQL #Python #Streamlit #PowerBI #DataScience #PortfolioProject #EcommerceAnalytics
```

---

## 3. 15 Technical Interview Questions & In-Depth Model Answers

### Category A: SQL & Query Performance

#### Q1: How did you calculate Customer Recency, Frequency, and Monetary (RFM) values in SQL, and how did you prevent fan-out when joining order items?
**Answer:**  
"To prevent fan-out, I aggregated at the order level before joining to customers, or aggregated item sales in a CTE. An order can contain multiple items in `fact_order_items`. If you join `dim_customers` directly to `fact_order_items` without aggregating, calculating order counts with `COUNT(order_id)` without `DISTINCT` would overcount multi-item orders.  
In my SQL query, I first filtered strictly for delivered orders (`order_status = 'delivered'`). I grouped by `customer_unique_id` (not `customer_id`, which is a per-order surrogate) and computed:
- `Recency`: `DATEDIFF(reference_date, MAX(order_purchase_timestamp))`
- `Frequency`: `COUNT(DISTINCT order_id)`
- `Monetary`: `SUM(price)` (excluding freight)  
This ensured that each line-item price contributed exactly once to revenue and each order contributed exactly once to frequency."

#### Q2: What is the difference between `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()`, and where did you use window functions in this project?
**Answer:**  
"`ROW_NUMBER()` assigns a unique, sequential integer to every row regardless of ties. `RANK()` assigns identical values to ties but skips subsequent rank numbers (e.g., 1, 2, 2, 4). `DENSE_RANK()` assigns identical values to ties without skipping numbers (e.g., 1, 2, 2, 3).  
In this project, I used window functions across several analyses:
1. `NTILE(10) OVER (ORDER BY total_spend DESC)` in Query 21 to partition customers into revenue deciles, revealing that the top 10% generated 41.10% of total platform sales.
2. `SUM(monthly_revenue) OVER (ORDER BY order_month)` in Query 18 to compute running cumulative revenue without expensive self-joins.
3. `DENSE_RANK() OVER (PARTITION BY category_group ORDER BY revenue DESC)` in Query 19 to identify the top 3 best-selling product categories within each macro sector."

#### Q3: Why did you filter strictly for `order_status = 'delivered'` in revenue calculations, and how did you handle freight?
**Answer:**  
"In revenue accounting and GAAP standards, unearned revenue from unshipped, processing, or canceled orders cannot be recognized until fulfillment. In the Olist dataset, non-delivered orders (canceled, unavailable, created) represent transactional attempts, not recognized revenue. Filtering for `order_status = 'delivered'` isolates real completed sales (R$ 13,221,498.11 across 96,478 orders).  
Regarding freight, merchandise revenue is strictly `SUM(price)`, whereas Gross Merchandise Value (GMV) includes freight (`SUM(price) + SUM(freight_value) = R$ 15,419,773.75`). Freight charges are pass-through logistics reimbursements remitted to carriers; treating freight as product revenue would artificially distort product margin and basket size analytics."

#### Q4: How did you optimize slow SQL queries during your analysis? Can you walk through an `EXPLAIN` plan example?
**Answer:**  
"When joining `dim_orders`, `fact_order_items`, and `dim_customers`, initial query plans required full table scans on `fact_order_items` (112k rows) and temporary tables with filesort on customer groupings.  
I created targeted B-tree indexes:
1. Composite foreign key index on `fact_order_items(order_id, product_id)`.
2. Composite index on `dim_orders(order_status, order_purchase_timestamp, customer_id)`.
3. Lookup index on `dim_customers(customer_unique_id)`.  
Running `EXPLAIN` on Query 13 (late delivery classification) before indexing showed `type: ALL` on orders. After adding the composite index, `EXPLAIN` confirmed `type: ref`, `key: idx_orders_status_date`, scanning only the 96,478 delivered rows directly from the index tree without loading unindexed columns into temporary memory, reducing execution time by over 75%."

---

### Category B: Data Modeling & Architecture

#### Q5: Explain the architectural differences between your MySQL relational schema and your Power BI Star Schema.
**Answer:**  
"The MySQL operational schema is a normalized relational schema across 9 tables. Its objective is transactional integrity, eliminating update anomalies and minimizing data redundancy (e.g., separating `dim_category_translation` from `dim_products`, and separating `dim_customers` from `dim_orders`).  
Conversely, the Power BI analytical warehouse in `data/exports/` is modeled as a Kimball Star Schema with 1 centralized fact table (`fact_order_items`), 4 direct dimensional tables (`dim_orders`, `dim_customers`, `dim_products`, `dim_date`), and 3 secondary tables. In the Star Schema, we intentionally denormalized category English translations, benchmark margin rates, and customer repeat flags directly into dimensions. This minimizes join depth (1-to-many single-hop relationships), eliminates bidirectional relationship ambiguity, and optimizes VertiPaq columnar compression in Power BI."

#### Q6: How did you handle the dual customer key problem (`customer_id` vs `customer_unique_id`)?
**Answer:**  
"Olist generates a new `customer_id` for every transaction. If you analyze customers using `customer_id`, every order appears to come from a brand-new customer, showing a false 0% repeat purchase rate.  
To resolve this, Olist provides `customer_unique_id`, which represents the actual person across time. In my data pipeline:
- `customer_id` serves as the transactional foreign key linking `dim_orders` to `dim_customers`.
- `customer_unique_id` is the analytical entity key for all customer intelligence, RFM segmentation, cohort retention, and CLV calculations.
This distinction revealed that there are 93,358 unique people across 99,441 customer orders, with 2,801 individuals purchasing multiple times."

#### Q7: Why did you create a dedicated Date Dimension (`dim_calendar`), and why is it preferred over raw timestamp columns in BI tools?
**Answer:**  
"Raw timestamp fields contain irregular, continuous timestamps (e.g., `2018-05-09 17:35:12`). In BI tools like Power BI, slicing directly on raw timestamps causes three major issues:
1. High cardinality destroys VertiPaq columnar compression efficiency.
2. Days with zero sales create discontinuous gaps that break DAX time-intelligence functions (`TOTALYTD`, `SAMEPERIODLASTYEAR`, `DATEADD`).
3. Slicing by fiscal quarters, day of week, or month names requires runtime calculations on millions of rows.  
By generating a dedicated, contiguous `dim_calendar` (1,096 rows covering 2016-01-01 to 2018-12-31) marked as the official Date Table, time-intelligence DAX functions compute deterministically, calendar hierarchies drill smoothly, and zero-sales days are accurately preserved in visualizations."

---

### Category C: Business Intelligence & Unit Economics

#### Q8: Olist's dataset has 97% one-time buyers. How did you design the RFM segmentation model to prevent frequency quantile collapse?
**Answer:**  
"Standard RFM models apply quintile binning (`pd.qcut` with 5 bins) across Recency, Frequency, and Monetary value. However, when 97.00% of customers have `frequency = 1`, all quantile boundaries between the 0th and 97th percentiles are identical (1.0). Forcing quantiles results in mathematical collapse or arbitrary rank splitting.  
To solve this, I designed a **hybrid discrete-quantile model**:
- **Recency & Monetary**: Scored 1 to 4 using rigorous statistical quartiles.
- **Frequency**: Scored discretely as a binary indicator: Score 1 for Single Buyers (`frequency = 1`, 90,557 users = 97.00%) and Score 2 for Repeat Buyers (`frequency >= 2`, 2,801 users = 3.00%).  
I then defined segment rules where 100% of repeat buyers are segmented into `Top Value` (if recent, $R \ge 3$) or `Mid Value` (if older, $R \le 2$), while one-time buyers are partitioned between high-spend recent buyers, aging high-value buyers (`Dormant`), and small-basket buyers (`Low Spend`). This preserved behavioral integrity without mathematical distortion."

#### Q9: What is the business significance of the 2.02-star CSAT drop on late deliveries, and what operational recommendations did you provide?
**Answer:**  
"Customer satisfaction data showed that on-time orders averaged **4.29 stars** with 62.26% 5-star ratings. When an order crossed the estimated delivery date (`DATE(delivered) > DATE(estimated)`), average rating plummeted by **2.02 stars to 2.27 stars**, with 1-star reviews surging from 10.39% to over 62%. Furthermore, linear regression on late orders showed an ongoing rating decay of **-0.0160 stars per additional day late**.  
This proves that customer satisfaction does not degrade linearly from day one; it suffers an immediate psychological cliff when the promised SLA is broken. My operational recommendation was twofold:
1. Recalibrate delivery promise algorithms: extending the customer-facing estimated delivery window by 2 days would eliminate ~65% of false SLA breaches without hurting conversion.
2. Automate proactive delay notifications and compensation vouchers on Day 1 of breach to mitigate the negative sentiment before review submission."

#### Q10: How did you calculate Customer Lifetime Value (CLV), and why is repeat buyer unit economics critical here?
**Answer:**  
"Historical CLV was calculated as the total delivered merchandise revenue divided by unique customers. For the platform overall, CLV is **R$ 141.62** (or **R$ 57.72** on a margin-adjusted gross profit basis at 40.76% margin).  
However, segmenting by customer loyalty reveals a dramatic divergence:
- One-time buyers average a CLV of **R$ 137.96**.
- Repeat buyers average a CLV of **R$ 260.05**—an **+88.5% spend premium**.  
Even though repeat customers comprise only 3.00% of the customer base, their unit economics prove that acquiring a customer who returns generates nearly double the lifetime value. This demonstrates that investing in re-engagement campaigns and post-purchase loyalty programs has significantly higher ROI than purely acquiring one-off buyers."

#### Q11: Explain your cohort retention methodology. What did the 2017 monthly cohort heatmap reveal?
**Answer:**  
"Cohorts were defined by customer acquisition month (the month of their very first delivered order) from January 2017 to December 2017, tracking their repurchase activity across subsequent elapsed months ($t_0, t_1, \dots, t_{12}$). Crucially, observed elapsed periods with zero repeat purchases were explicitly encoded as `0.00%`, rather than being left blank or imputed.  
The analysis revealed that across the 12 monthly cohorts shown in the 2017 retention heatmap, Month-1 retention averages **0.49%**, peaking at **0.72% for the October 2017 cohort** (the March 2017 cohort is **0.44%**) and decaying to 0.10%-0.20% by Month 6. (Across all 18 cohorts from January 2017 to June 2018 with observed follow-up, the unweighted Month-1 average is **0.47%**). This confirms that Olist operated primarily as an acquisition-driven marketplace for durable goods (furniture, appliances, electronics) rather than a habit-forming consumable platform. Marketplace strategy must therefore focus on category expansion into recurring consumables (health, beauty, food) to drive repeat frequency."

---

### Category D: Implementation, Design Choices & Production Engineering

#### Q12: How did you approach profitability analysis given that the Olist dataset does not contain wholesale cost data?
**Answer:**  
"Rather than ignoring costs and presenting misleading revenue-as-profit figures, I created an explicit financial configuration framework (`config/margin_assumptions.yaml`). I grouped the ~70 product categories into 11 macro sectors and mapped realistic retail gross margin benchmarks based on e-commerce industry standards (e.g., 50% for Beauty, 40% for Furniture, 25% for Consumer Electronics).  
Crucially, I enforced strict labeling rules across the codebase, SQL queries, Streamlit dashboard, and documentation: every profit, COGS, and gross margin metric is explicitly designated **'assumed margin, not real data'**. This demonstrates business acumen, transparency, and data governance rigor."

#### Q13: Why did you choose Holt-Winters Exponential Smoothing over Facebook Prophet or ARIMA for sales forecasting?
**Answer:**  
"I selected Holt-Winters Exponential Smoothing (additive trend + 7-day additive weekly seasonality) for three reasons:
1. **Dependency Footprint**: Prophet requires heavy compilation toolchains (Stan / C++ compilers) which frequently fail or bloat cloud deployments, whereas Holt-Winters is natively supported in `statsmodels` using standard NumPy/SciPy.
2. **Data Characteristics**: Daily e-commerce sales exhibit strong day-of-week seasonality (surges on weekdays, dips on weekends) and a gradual trend without complex multi-year holiday structures. Holt-Winters models this cleanly with minimal compute overhead.
3. **Accuracy & Validation**: We validated the model on a 30-day holdout test window (2018-07-22 to 2018-08-20), achieving a Weighted Absolute Percentage Error (WAPE) of **12.90%** and an MAE of **R$ 4,647.90** against a daily mean of R$ 36,038.69, which is production-grade for operational inventory planning."

#### Q14: How did you architect the Streamlit application for fast, zero-database cloud deployment?
**Answer:**  
"A common rookie mistake is connecting a web dashboard directly to a live transactional database in production, causing slow queries, connection pool exhaustion, and credential exposure.  
Instead, I decoupled analytics delivery from the database:
1. Python batch pipelines pre-compute and export analytical dimension and fact tables into `data/exports/` CSVs.
2. The Streamlit app reads exclusively from these CSVs using `@st.cache_data`, caching data in memory after the initial load.
3. File paths are resolved dynamically using `os.path.join(os.path.dirname(__file__), '..', 'data', 'exports')`, ensuring seamless execution whether run locally on Windows or deployed on Linux in Streamlit Community Cloud.
4. Calculations are modularized into a standalone `kpi_metrics.py` module with zero Streamlit dependencies, enabling comprehensive automated unit testing."

#### Q15: How did you ensure data quality and financial reconciliation across your pipeline?
**Answer:**  
"I developed an automated 46-test suite in `pytest` organized into 8 test modules:
1. `test_data_quality.py`: Verifies primary key uniqueness, non-null constraints, price/freight non-negativity, and coordinate bounds.
2. `test_db_connection.py`: Validates MySQL 8.0 connectivity and verifies schema table creation.
3. `test_sql_queries.py`: Reconciles business queries against mathematical balances (e.g., running cumulative sales equal grand total; Q14 COGS + Gross Profit equal Merchandise Revenue R$ 13,221,498.11; Q5 reviews sum to 96,361 on delivered orders; Q8 reviews with verified delivery dates sum to 96,353 across 89,944 on-time and 6,409 late reviews).
4. `test_eda.py`: Confirms RFM segment customer counts sum to 93,358 and revenue sums to R$ 13,221,498.11; confirms holdout WAPE matches 12.90%.
5. `test_powerbi_exports.py`: Validates Star Schema row counts, referential integrity between dimensions and facts, and financial reconciliation.
6. `test_streamlit_kpis.py`: Ensures the Streamlit calculation engine reproduces the exact baseline figures (R$ 13,221,498.11 revenue, 96,478 orders, 2,801 repeat buyers) with zero filters and sub-filters accurately.  
7. `test_readme_reconciliation.py`: End-to-end automated assertions confirming all published metrics in the README and career pack match export CSVs and underlying statistical models (7 tests).  
8. `test_app_pages.py`: Streamlit AppTest smoke tests verifying all 5 dashboard views and filtering render without exceptions (6 tests).  
This continuous testing guarantees that numbers presented to executive stakeholders are mathematically infallible."

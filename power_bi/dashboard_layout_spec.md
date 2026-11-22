# Power BI Executive Dashboard Layout & Implementation Guide

## 1. Executive Dashboard Architecture

The **E-Commerce Sales & Customer Intelligence Dashboard** is designed for C-suite executives, VP of Growth, Head of Logistics, and Category Managers. Built on a standardized **16:9 widescreen canvas (1280 x 720 px)**, it provides an intuitive, interactive analytical experience across **4 core report pages**:

```text
├── Page 1: Executive KPI & Sales Performance Overview
├── Page 2: Customer Intelligence & RFM Segmentation
├── Page 3: Product Portfolio, Category Margins & Pareto Distribution
└── Page 4: Logistics SLA, Carrier Performance & CSAT Impact
```

---

## 2. Design System, Typography & Corporate Color Palette

### Color Palette Specification
| Role | Color Name | Hex Code | Usage |
|:---|:---|:---:|:---|
| **Primary Theme** | Dark Slate Navy | `#1B2A4A` | Header banners, KPI card labels, primary series |
| **Secondary Accent** | Ocean Blue | `#2980B9` | Historical revenue bars, secondary chart elements |
| **Accent Positive** | Emerald Green | `#27AE60` | On-time delivery, gross profit, promoter scores, top value |
| **Accent Warning** | Ochre Amber | `#F39C12` | Moderate delays, dormant customers, mid-tier margin |
| **Accent Negative** | Crimson Coral | `#E74C3C` | SLA breaches, cancellations, detractors, low-spend customers |
| **Canvas Background**| Crisp Off-White | `#F8F9FA` | Report background behind visual cards |
| **Visual Container** | Pure White | `#FFFFFF` | Visual card background with 1px border (`#E2E8F0`) & soft shadow |

### Typography Standard
- **Font Family**: `Segoe UI` (native Power BI high-legibility sans-serif)
- **KPI Big Number Callout**: `24 pt Bold` (`#1B2A4A`)
- **Visual Title**: `12 pt Semi-Bold` (`#2C3E50`)
- **Axis & Data Labels**: `9 pt Regular` (`#64748B`)
- **Slicers & Controls**: `10 pt Regular` (`#1B2A4A`)

---

## 3. Page-by-Page Visual Layout Specifications

### Page 1: Executive KPI & Sales Performance Overview
**Goal**: High-level platform health check displaying revenue throughput, GMV, order volume, AOV, and monthly growth trends.

#### Global Header & Filter Bar ($Y = 0 \text{ to } 70\text{ px}$)
- **Title Block** ($X=20, Y=15, W=400, H=45$): Text box `"E-Commerce Executive Sales Performance Overview"` (18 pt Bold Navy) + Subtitle `"Delivered Merchandise & Growth Tracking | Currency: Brazilian Reais (R$)"` (10 pt Gray).
- **Year Slicer** ($X=700, Y=15, W=160, H=45$): Horizontal tile slicer on `dim_calendar[Year]` (Options: `All`, `2016`, `2017`, `2018`).
- **Category Group Slicer** ($X=880, Y=15, W=200, H=45$): Dropdown slicer on `dim_products[category_group]`.
- **Order Status Slicer** ($X=1100, Y=15, W=160, H=45$): Dropdown slicer on `dim_orders[order_status]` (Default: `delivered`).

#### KPI Summary Cards Row ($Y = 80 \text{ to } 180\text{ px}$)
| Visual # | Card Name | Metric / DAX Measure | Dimensions ($X, Y, W, H$) | Target Value (All Time) |
|:---|:---|:---|:---:|---:|
| **Card 1.1** | Total Merchandise Revenue | `[Total Delivered Merchandise Revenue]` | $X=20, Y=80, W=230, H=100$ | **R$ 13.22M** |
| **Card 1.2** | Gross Merchandise Value (GMV) | `[Gross Merchandise Value (GMV)]` | $X=270, Y=80, W=230, H=100$ | **R$ 15.42M** |
| **Card 1.3** | Total Delivered Orders | `[Total Delivered Orders]` | $X=520, Y=80, W=230, H=100$ | **96,478** |
| **Card 1.4** | Average Order Value (AOV) | `[Average Order Value (AOV)]` | $X=770, Y=80, W=230, H=100$ | **R$ 137.04** |
| **Card 1.5** | Blended Gross Margin | `[Blended Gross Margin % [Assumed]]` | $X=1020, Y=80, W=240, H=100$ | **40.76%** *(Assumed)* |

#### Main Charts Area ($Y = 200 \text{ to } 690\text{ px}$)
- **Visual 1.6: Monthly Revenue Trend & MoM Growth %** ($X=20, Y=200, W=820, H=310$)
  - **Type**: Line and Clustered Column Chart.
  - **Shared X-Axis**: `dim_calendar[YearMonth]` (sorted by `YearMonthInt`).
  - **Column Values**: `[Total Delivered Merchandise Revenue]` (Bars in `#2980B9`).
  - **Line Values**: `[Revenue MoM Growth %]` (Line in `#E67E22` with markers).
  - **Insight Callout**: Highlights the Black Friday surge in November 2017 (R$ 1.16M revenue).
- **Visual 1.7: Sales Breakdown by Payment Method** ($X=860, Y=200, W=400, H=310$)
  - **Type**: Donut Chart.
  - **Legend**: `fact_order_payments[payment_type]`.
  - **Values**: `[Total Payment Transaction Value]`.
  - **Data Labels**: Category & Percentage of Total (Credit Card ~74.0%, Boleto ~19.0%, Voucher ~5.6%, Debit ~1.5%).
- **Visual 1.8: Top 10 Macro Category Revenue Contribution** ($X=20, Y=530, W=620, H=170$)
  - **Type**: Horizontal Clustered Bar Chart.
  - **Y-Axis**: `dim_products[category_group]`.
  - **X-Axis**: `[Total Delivered Merchandise Revenue]` (Sorted descending, Top 10).
  - **Data Labels**: Displayed in `R$ Millions`.
- **Visual 1.9: Top 10 Brazilian States by Revenue** ($X=660, Y=530, W=600, H=170$)
  - **Type**: Clustered Column Chart.
  - **X-Axis**: `dim_customers[customer_state]`.
  - **Y-Axis**: `[Total Delivered Merchandise Revenue]`.
  - **Insight Callout**: SP (São Paulo) powers >37% of platform GMV, followed by RJ and MG.

---

### Page 2: Customer Intelligence & RFM Segmentation
**Goal**: Unpack customer acquisition, RFM distribution, repeat purchase patterns, and customer lifetime value (CLV).

#### KPI Summary Cards Row ($Y = 80 \text{ to } 180\text{ px}$)
| Visual # | Card Name | Metric / DAX Measure | Dimensions ($X, Y, W, H$) | Target Value (All Time) |
|:---|:---|:---|:---:|---:|
| **Card 2.1** | Total Unique Customers | `[Total Unique Customers]` | $X=20, Y=80, W=230, H=100$ | **93,358** |
| **Card 2.2** | Repeat Customers | `[Repeat Customers Count]` | $X=270, Y=80, W=230, H=100$ | **2,801** |
| **Card 2.3** | Repeat Purchase Rate | `[Repeat Customer Rate %]` | $X=520, Y=80, W=230, H=100$ | **3.00%** |
| **Card 2.4** | Historical Baseline CLV | `[Historical Customer Lifetime Value (CLV)]` | $X=770, Y=80, W=230, H=100$ | **R$ 141.62** |
| **Card 2.5** | Repeat Customer CLV Premium | `[Repeat Customer CLV]` | $X=1020, Y=80, W=240, H=100$ | **R$ 260.05** (+88.5%) |

#### Main Charts Area ($Y = 200 \text{ to } 690\text{ px}$)
- **Visual 2.6: RFM Segment Customer Volume vs Revenue Share** ($X=20, Y=200, W=600, H=310$)
  - **Type**: Clustered Column Chart.
  - **X-Axis**: `dim_customers[rfm_segment]` (Order: `Top Value`, `Mid Value`, `Dormant`, `Low Spend`).
  - **Y-Axis**: `[Total Unique Customers]` and `[Total Delivered Merchandise Revenue]`.
  - **Insight Note**: Shows that Top Value + Mid Value hold >44% of revenue despite low total buyer share.
- **Visual 2.7: RFM Customer Profile Matrix** ($X=640, Y=200, W=620, H=310$)
  - **Type**: Matrix Visual.
  - **Rows**: `dim_customers[rfm_segment]`.
  - **Values**:
    - `Customer Count`: `[Total Unique Customers]`
    - `Repeat Buyers`: `[Repeat Customers Count]`
    - `Repeat %`: `[Repeat Customer Rate %]`
    - `Avg Recency (Days)`: `AVERAGE(dim_customers[rfm_recency_days])`
    - `Total Revenue`: `[Total Delivered Merchandise Revenue]`
    - `Revenue Share %`: `DIVIDE([Total Delivered Merchandise Revenue], CALCULATE([Total Delivered Merchandise Revenue], ALL(dim_customers[rfm_segment])))`
    - `Avg Spend (BRL)`: `DIVIDE([Total Delivered Merchandise Revenue], [Total Unique Customers])`
  - **Formatting**: Conditional data bars on Total Revenue and heat gradient on Repeat %.
- **Visual 2.8: One-Time vs Repeat Customer Spend Distribution** ($X=20, Y=530, W=500, H=170$)
  - **Type**: Clustered Bar Chart.
  - **Y-Axis**: `Customer Frequency Tier` (`Single Order Buyer` vs `Repeat Buyer >=2`).
  - **X-Axis**: Average Spend per Customer (`R$ 137.96` vs `R$ 260.05`).
- **Visual 2.9: Cohort Retention Overview Heatmap Table** ($X=540, Y=530, W=720, H=170$)
  - **Type**: Matrix Visual displaying 2017 monthly acquisition cohorts across Month 0 to Month 12 retention rates.
  - **Formatting**: Background color conditional scale (0.00% light yellow to 1.00% dark teal). Observed zeros formatted as `0.00%`.

---

### Page 3: Product Portfolio, Category Margins & Pareto Distribution
**Goal**: Granular merchandise intelligence, 80/20 product concentration, and category profitability using assumed benchmark COGS.

#### KPI Summary Cards Row ($Y = 80 \text{ to } 180\text{ px}$)
| Visual # | Card Name | Metric / DAX Measure | Dimensions ($X, Y, W, H$) | Target Value (All Time) |
|:---|:---|:---|:---:|---:|
| **Card 3.1** | Total SKUs Catalog | `DISTINCTCOUNT(dim_products[product_id])` | $X=20, Y=80, W=230, H=100$ | **32,951** |
| **Card 3.2** | Pareto 80% SKU Core | `"8,352 SKUs"` | $X=270, Y=80, W=230, H=100$ | **25.93%** of catalog |
| **Card 3.3** | Estimated Gross Profit | `[Estimated Gross Profit (BRL) [Assumed]]` | $X=520, Y=80, W=230, H=100$ | **R$ 5.39M** *(Assumed)* |
| **Card 3.4** | Highest Margin Sector | `"Fashion & Apparel"` | $X=770, Y=80, W=230, H=100$ | **55.0%** margin |
| **Card 3.5** | Top Profit Dollar Sector | `"Health, Beauty & Personal"` | $X=1020, Y=80, W=240, H=100$ | **R$ 684.9K** GP |

#### Main Charts Area ($Y = 200 \text{ to } 690\text{ px}$)
- **Visual 3.6: Revenue vs Assumed Gross Profit by Macro Sector** ($X=20, Y=200, W=720, H=310$)
  - **Type**: Clustered Bar Chart.
  - **Y-Axis**: `dim_products[category_group]`.
  - **X-Axis**: `[Total Delivered Merchandise Revenue]` (Blue `#2980B9`) and `[Estimated Gross Profit (BRL) [Assumed]]` (Green `#27AE60`).
  - **Data Labels**: Currency in Thousands (`R$ K`).
  - **Subtitle**: *"Financial Note: Profitability uses benchmark assumptions, not actual accounting COGS"*.
- **Visual 3.7: Category Margin Rate vs Sales Volume Matrix** ($X=760, Y=200, W=500, H=310$)
  - **Type**: Scatter / Bubble Chart.
  - **X-Axis**: `[Total Items Sold]`.
  - **Y-Axis**: `[Blended Gross Margin % [Assumed]]`.
  - **Bubble Size**: `[Total Delivered Merchandise Revenue]`.
  - **Legend**: `dim_products[category_group]`.
  - **Reference Lines**: Horizontal line at 40.76% (Platform Average Margin).
- **Visual 3.8: Top 15 Best-Selling Products by Revenue** ($X=20, Y=530, W=1240, H=170$)
  - **Type**: Table Visual.
  - **Columns**: `product_id`, `product_category_name_english`, `category_group`, `Units Sold` (`[Total Items Sold]`), `Merchandise Revenue` (`[Total Delivered Merchandise Revenue]`), `Assumed GP` (`[Estimated Gross Profit (BRL) [Assumed]]`), `Margin %` (`[Blended Gross Margin % [Assumed]]`).
  - **Sorting**: Total Delivered Merchandise Revenue descending.

---

### Page 4: Logistics SLA, Carrier Performance & CSAT Impact
**Goal**: Logistics fulfillment monitoring, carrier SLA compliance, delivery delay distributions, and customer satisfaction review score degradation.

#### KPI Summary Cards Row ($Y = 80 \text{ to } 180\text{ px}$)
| Visual # | Card Name | Metric / DAX Measure | Dimensions ($X, Y, W, H$) | Target Value (All Time) |
|:---|:---|:---|:---:|---:|
| **Card 4.1** | On-Time Delivery Rate | `[On-Time Delivery Rate %]` | $X=20, Y=80, W=230, H=100$ | **93.23%** |
| **Card 4.2** | SLA Delayed Orders | `[Delayed Delivered Orders]` | $X=270, Y=80, W=230, H=100$ | **6,535** (6.77%) |
| **Card 4.3** | Average Lead Time | `[Average Delivery Lead Time (Days)]` | $X=520, Y=80, W=230, H=100$ | **12.5 days** |
| **Card 4.4** | On-Time CSAT Rating | `"4.29 Stars"` | $X=770, Y=80, W=230, H=100$ | **4.29** (9.3% detractors) |
| **Card 4.5** | Delayed CSAT Rating | `"2.27 Stars"` | $X=1020, Y=80, W=240, H=100$ | **2.27** (-2.02 star drop) |

#### Main Charts Area ($Y = 200 \text{ to } 690\text{ px}$)
- **Visual 4.6: Average CSAT Score across Delay Performance Tiers** ($X=20, Y=200, W=600, H=310$)
  - **Type**: Clustered Column Chart.
  - **X-Axis**: Fulfillment Performance Tier (`On-Time / Early <=0d`, `Minor 1-3d`, `Moderate 4-7d`, `High 8-14d`, `Severe 15+d`).
  - **Y-Axis**: `[Average Customer Satisfaction (CSAT)]` (Formatted with 2 decimals).
  - **Colors**: Green for On-Time (`4.29`), Amber for Minor (`2.57`), Dark Red for Severe (`1.61`).
  - **Insight Box**: Highlights the immediate 2.02-star drop on day 1 of delay.
- **Visual 4.7: Review Rating Breakdown: On-Time vs Delayed** ($X=640, Y=200, W=620, H=310$)
  - **Type**: 100% Stacked Bar Chart.
  - **Y-Axis**: Delivery Status (`On-Time / Early` vs `Delayed / Late`).
  - **X-Axis**: Review Score Distribution (1 Star, 2 Stars, 3 Stars, 4 Stars, 5 Stars).
  - **Colors**: 1-2 Stars in Crimson Red (`#E74C3C`), 3 Stars in Gray (`#BDC3C7`), 4-5 Stars in Green (`#27AE60`).
  - **Clear Finding**: On-time orders are 62.3% 5-star promoters; delayed orders are 62.4% 1-2 star detractors.
- **Visual 4.8: Average Delivery Lead Time by Destination State** ($X=20, Y=530, W=600, H=170$)
  - **Type**: Clustered Bar Chart.
  - **Y-Axis**: `dim_customers[customer_state]` (Top 10 highest transit states: RR, AP, AM, etc. vs SP ~8.3 days).
  - **X-Axis**: `[Average Delivery Lead Time (Days)]`.
- **Visual 4.9: OLS Decay Curve: Rating Decline per Day of Delay** ($X=640, Y=530, W=620, H=170$)
  - **Type**: Line / Area Chart.
  - **X-Axis**: Days Delayed Past SLA (1 to 30 days).
  - **Y-Axis**: Average CSAT Score.
  - **Trendline Annotation**: *"OLS Linear Regression on Late Orders: Slope = -0.0160 stars per day late"*.

---

## 4. Step-by-Step Power BI Desktop Tutorial (Windows Free Version)

Follow this complete, beginner-to-intermediate guide to import the data and construct the data model in **Power BI Desktop**:

### Step 1: Open Power BI Desktop & Load CSVs
1. Launch **Power BI Desktop** on Windows.
2. In the Home Ribbon, click **Get Data** $\rightarrow$ select **Text/CSV** $\rightarrow$ click **Connect**.
3. Browse to your project repository directory:
   `c:\Users\khana\Desktop\DAP 1\data\exports\`
4. Import the following 8 CSV files one by one:
   - `dim_calendar.csv`
   - `dim_orders.csv`
   - `dim_customers.csv`
   - `dim_products.csv`
   - `dim_sellers.csv`
   - `fact_order_items.csv`
   - `fact_order_payments.csv`
   - `fact_order_reviews.csv`
5. On the preview modal for each file, verify encoding is **65001: Unicode (UTF-8)** and delimiter is **Comma**, then click **Load** (or **Transform Data** if you wish to inspect column datatypes in Power Query).

### Step 2: Configure Model Relationships in Model View
1. Click the **Model View** icon on the left vertical navigation bar (the third icon with relationship boxes).
2. Arrange the tables in the canvas into a Star Schema layout:
   - Place `dim_orders`, `dim_customers`, `dim_products`, `dim_sellers`, and `dim_calendar` on the outer layer.
   - Place `fact_order_items`, `fact_order_payments`, and `fact_order_reviews` in the center.
3. Establish the relationships by dragging and dropping primary keys onto foreign keys:
   - **dim_calendar[Date]** $\rightarrow$ **dim_orders[order_purchase_date]**:
     - Cardinality: `One to many (1:*)`
     - Cross filter direction: `Single`
     - Check: `Make this relationship active`
   - **dim_calendar[Date]** $\rightarrow$ **dim_orders[order_delivered_customer_date_only]**:
     - Cardinality: `One to many (1:*)`
     - Cross filter direction: `Single`
     - Uncheck `Make this relationship active` (Inactive relationship for `USERELATIONSHIP` use).
   - **dim_customers[customer_id]** $\rightarrow$ **dim_orders[customer_id]**:
     - Cardinality: `One to many (1:*)` | Cross filter: `Single` | Active.
   - **dim_orders[order_id]** $\rightarrow$ **fact_order_items[order_id]**:
     - Cardinality: `One to many (1:*)` | Cross filter: `Single` | Active.
   - **dim_orders[order_id]** $\rightarrow$ **fact_order_payments[order_id]**:
     - Cardinality: `One to many (1:*)` | Cross filter: `Single` | Active.
   - **dim_orders[order_id]** $\rightarrow$ **fact_order_reviews[order_id]**:
     - Cardinality: `One to many (1:*)` | Cross filter: `Single` | Active.
   - **dim_products[product_id]** $\rightarrow$ **fact_order_items[product_id]**:
     - Cardinality: `One to many (1:*)` | Cross filter: `Single` | Active.
   - **dim_sellers[seller_id]** $\rightarrow$ **fact_order_items[seller_id]**:
     - Cardinality: `One to many (1:*)` | Cross filter: `Single` | Active.

### Step 3: Create the Dedicated `_Measures` Table
1. In the **Home** Ribbon, click **Enter Data**.
2. Rename `Table1` to `_Measures`. Rename `Column1` to `Placeholder`.
3. Click **Load**.
4. In the Data pane on the right, right-click `_Measures` and select **New measure**.
5. Copy and paste the DAX measure formulas from `power_bi/dax_measures.md`.
6. For each created measure:
   - Select the measure in the Data pane.
   - In the **Measure tools** ribbon, enter the **Display folder** (e.g., `01 Financial KPIs`).
   - Set the formatting:
     - Currencies: Select Format dropdown $\rightarrow$ **Currency**, custom string: `R$ #,##0.00; -R$ #,##0.00; "R$ 0.00"`.
     - Percentages: Click the `%` icon, set decimals to `2`.
     - Counts: Click the comma `,` icon, set decimals to `0`.
7. Once your first real measure is added, delete the `Placeholder` column. The `_Measures` table will automatically jump to the top of your Data pane with a calculator icon!

### Step 4: Configure Sort By Columns
To ensure chronological and ordinal sorting in visuals:
1. In `dim_calendar`, select `MonthName` $\rightarrow$ in the **Column tools** ribbon, click **Sort by column** $\rightarrow$ choose `Month`.
2. In `dim_calendar`, select `YearMonth` $\rightarrow$ click **Sort by column** $\rightarrow$ choose `YearMonthInt`.
3. In `dim_calendar`, select `DayName` $\rightarrow$ click **Sort by column** $\rightarrow$ choose `DayOfWeek`.

### Step 5: Build Visuals and Slicers
1. Add 4 pages to the report tab bar at the bottom:
   - `Sales Performance`
   - `Customer Intelligence`
   - `Products & Profitability`
   - `Logistics & CSAT`
2. Follow the coordinates and visual field configurations detailed in Section 3 of this document.
3. Save your Power BI workbook as:
   `power_bi/ecommerce_analytics_dashboard.pbix`

# Data Dictionary: E-Commerce Sales & Customer Intelligence Analytics Platform

> **Currency Standard**: All monetary attributes (`price`, `freight_value`, `payment_value`, `cogs`, `gross_profit`) are denominated strictly in **Brazilian Reais (R$ / BRL)**.  
> **Source**: Brazilian E-Commerce Public Dataset by Olist (Kaggle), spanning orders from September 2016 to October 2018.  
> **Financial Labelling**: All cost of goods sold (`cogs`) and gross profit margins are benchmark assumptions defined in `config/margin_assumptions.yaml` (*assumed margin, not real data*).

---

## 1. Relational Database Schema (MySQL 8.0: `olist_ecommerce`)

The operational database implements a 3NF normalized schema across 9 relational tables with primary keys, foreign keys, and covering indexes.

### 1.1 `dim_orders` (Order Lifecycle Header)
*Granularity: 1 row per order (99,441 rows total; 96,478 delivered orders).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | **PK** / NOT NULL | Unique 32-character hexadecimal identifier for each customer transaction. |
| `customer_id` | `VARCHAR(32)` | **FK** / NOT NULL | Transactional customer surrogate key referencing `dim_customers(customer_id)`. |
| `order_status` | `VARCHAR(20)` | NOT NULL | Current order lifecycle status (`delivered`, `shipped`, `canceled`, `invoiced`, `processing`, `unavailable`). |
| `order_purchase_timestamp` | `DATETIME` | NOT NULL | Exact date and time when the customer placed the order. |
| `order_approved_at` | `DATETIME` | NULL | Timestamp when the payment gateway cleared the order transaction. |
| `order_delivered_carrier_date` | `DATETIME` | NULL | Timestamp when the order was handed over to the logistics fulfillment carrier. |
| `order_delivered_customer_date` | `DATETIME` | NULL | Actual timestamp when the customer received the package at their delivery address. |
| `order_estimated_delivery_date` | `DATETIME` | NOT NULL | Promised SLA delivery deadline provided to the customer during checkout (00:00:00 time). |

---

### 1.2 `dim_customers` (Customer Directory)
*Granularity: 1 row per order-customer instance (99,441 rows total; 93,358 unique customer individuals).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | **PK** / NOT NULL | Transaction-specific customer key created per order. |
| `customer_unique_id` | `VARCHAR(32)` | NOT NULL | Persistent real-world individual customer identifier used to link repeat buyers across multiple orders. |
| `customer_zip_code_prefix` | `INT` | NOT NULL | First 5 digits of the Brazilian postal code (CEP). |
| `customer_city` | `VARCHAR(100)` | NOT NULL | City name of customer residence (normalized to lowercase). |
| `customer_state` | `VARCHAR(2)` | NOT NULL | Brazilian Federation state abbreviation (e.g., `SP`, `RJ`, `MG`). |

---

### 1.3 `fact_order_items` (Order Line-Item Transactions)
*Granularity: 1 row per order item (112,650 rows total; 110,197 delivered items).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | **PK, FK** / NOT NULL | References `dim_orders(order_id)`. Composite primary key component. |
| `order_item_id` | `INT` | **PK** / NOT NULL | Sequential line-item sequence number within the order (`1`, `2`, `3`...). |
| `product_id` | `VARCHAR(32)` | **FK** / NOT NULL | Unique product identifier referencing `dim_products(product_id)`. |
| `seller_id` | `VARCHAR(32)` | **FK** / NOT NULL | Unique seller identifier referencing `dim_sellers(seller_id)`. |
| `shipping_limit_date` | `DATETIME` | NOT NULL | Deadline for seller to transfer the item to the carrier. |
| `price` | `DECIMAL(10,2)` | NOT NULL | Net merchandise item price in Brazilian Reais (R$). Excludes freight. |
| `freight_value` | `DECIMAL(10,2)` | NOT NULL | Shipping freight charge allocated to this specific item in Brazilian Reais (R$). |

---

### 1.4 `fact_order_payments` (Payment Settlements)
*Granularity: 1 row per payment transaction attempt (103,886 rows total; 100,487 delivered order payments).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | **PK, FK** / NOT NULL | References `dim_orders(order_id)`. Composite primary key component. |
| `payment_sequential` | `INT` | **PK** / NOT NULL | Payment sequence sequence index for orders split across multiple tender methods. |
| `payment_type` | `VARCHAR(30)` | NOT NULL | Tender instrument used (`credit_card`, `boleto`, `voucher`, `debit_card`). |
| `payment_installments` | `INT` | NOT NULL | Number of credit card billing installment installments selected by customer (1 to 24). |
| `payment_value` | `DECIMAL(10,2)` | NOT NULL | Total transaction value processed in this payment event in Brazilian Reais (R$). |

---

### 1.5 `fact_order_reviews` (Customer Satisfaction Surveys)
*Granularity: 1 row per survey evaluation response (99,224 rows total; 96,361 delivered order reviews).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `review_surrogate_id` | `INT` | **PK** / NOT NULL | Auto-incremented integer surrogate key resolving non-unique raw review IDs. |
| `review_id` | `VARCHAR(32)` | NOT NULL | Review event identifier from Olist customer app. |
| `order_id` | `VARCHAR(32)` | **FK** / NOT NULL | References `dim_orders(order_id)`. |
| `review_score` | `TINYINT` | NOT NULL | CSAT customer satisfaction rating on 1 to 5 integer scale. |
| `review_comment_title` | `VARCHAR(255)` | NULL | Optional customer review subject headline. |
| `review_comment_message` | `TEXT` | NULL | Free-form qualitative customer feedback text. |
| `review_creation_date` | `DATETIME` | NOT NULL | Date when the satisfaction survey link was dispatched to the customer. |
| `review_answer_timestamp` | `DATETIME` | NOT NULL | Date and time when the customer submitted their response. |

---

### 1.6 `dim_products` (Product Catalog & Profitability Benchmarks)
*Granularity: 1 row per product SKU (32,951 products).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | **PK** / NOT NULL | Unique 32-character product identifier. |
| `product_category_name` | `VARCHAR(100)` | NOT NULL | Category name in Portuguese (e.g., `cama_mesa_banho`). |
| `product_name_lenght` | `INT` | NULL | Character count of product title. |
| `product_description_lenght` | `INT` | NULL | Character count of product listing description. |
| `product_photos_qty` | `INT` | NULL | Count of product images published on listing. |
| `product_weight_g` | `DECIMAL(10,2)` | NULL | Product weight in grams. |
| `product_length_cm` | `DECIMAL(10,2)` | NULL | Physical length dimension in centimeters. |
| `product_height_cm` | `DECIMAL(10,2)` | NULL | Physical height dimension in centimeters. |
| `product_width_cm` | `DECIMAL(10,2)` | NULL | Physical width dimension in centimeters. |
| `product_category_name_english` | `VARCHAR(100)` | NOT NULL | Standardized English category name translated via lookup. |
| `category_group` | `VARCHAR(100)` | NOT NULL | Consolidated macro sector grouping (11 strategic categories). |
| `assumed_cogs_rate` | `DECIMAL(5,4)` | NOT NULL | Benchmark cost assumption rate (e.g., `0.5500` for Fashion). *Assumed, not real data*. |
| `assumed_gross_margin_rate` | `DECIMAL(5,4)` | NOT NULL | Benchmark margin rate (`1.0 - assumed_cogs_rate`). *Assumed, not real data*. |

---

### 1.7 `dim_sellers` (Merchant Directory)
*Granularity: 1 row per registered merchant seller (3,095 sellers).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `seller_id` | `VARCHAR(32)` | **PK** / NOT NULL | Unique 32-character seller identifier. |
| `seller_zip_code_prefix` | `INT` | NOT NULL | First 5 digits of merchant fulfillment center postal code. |
| `seller_city` | `VARCHAR(100)` | NOT NULL | City location of seller fulfillment hub. |
| `seller_state` | `VARCHAR(2)` | NOT NULL | Brazilian Federation state abbreviation of seller location. |

---

### 1.8 `dim_geolocation` (Geographic Coordinates Directory)
*Granularity: 1 row per unique postal code prefix (19,015 geographic postal clusters).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `geolocation_zip_code_prefix` | `INT` | **PK** / NOT NULL | First 5 digits of postal code. |
| `geolocation_lat` | `DECIMAL(10,6)` | NOT NULL | Cleaned median geographic latitude coordinate. |
| `geolocation_lng` | `DECIMAL(10,6)` | NOT NULL | Cleaned median geographic longitude coordinate. |
| `geolocation_city` | `VARCHAR(100)` | NOT NULL | Predominant municipality associated with postal prefix. |
| `geolocation_state` | `VARCHAR(2)` | NOT NULL | Brazilian Federation state abbreviation. |

---

### 1.9 `dim_category_translation` (Portuguese-to-English Mapping)
*Granularity: 1 row per Portuguese category name (71 categories).*

| Column Name | Data Type | Key / Nullable | Description & Business Rules |
| :--- | :--- | :--- | :--- |
| `product_category_name` | `VARCHAR(100)` | **PK** / NOT NULL | Original Portuguese category name. |
| `product_category_name_english` | `VARCHAR(100)` | NOT NULL | English translated category title. |

---

## 2. Power BI & Streamlit Analytical Data Model (`data/exports/`)

The dimensional warehouse deployed in `data/exports/` optimizes query performance and slicing efficiency via an analytical Star Schema.

### 2.1 `dim_orders.csv`
- **Grain**: 1 row per order (99,441 rows).
- **Columns**: `order_id`, `customer_id`, `order_status`, `order_purchase_date`, `order_delivered_customer_date_only`, `order_estimated_delivery_date_only`, `delivery_delay_days`, `is_delayed`, `delivery_lead_time_days`, `carrier_transit_time_days`.
- **Enriched Attributes**:
  - `delivery_delay_days`: Strict calendar day variance `DATEDIFF(order_delivered_customer_date, order_estimated_delivery_date)`. Positive values indicate SLA delivery delay; zero or negative values indicate on-time fulfillment.
  - `is_delayed`: Binary logistics SLA breach flag (`1` if `delivery_delay_days > 0`, else `0`).
  - `delivery_lead_time_days`: Total duration from purchase timestamp to customer doorstep delivery in decimal days.
  - `carrier_transit_time_days`: Duration from carrier dispatch to customer delivery in decimal days.

### 2.2 `dim_customers.csv`
- **Grain**: 1 row per transactional `customer_id` (99,441 rows; 93,358 unique people).
- **Columns**: `customer_id`, `customer_unique_id`, `customer_state`, `rfm_segment`, `is_repeat_customer`.
- **Enriched Attributes**:
  - `is_repeat_customer`: Binary loyalty indicator (`1` if unique customer completed $\ge 2$ delivered orders, else `0`).
  - `rfm_segment`: Segment classification (`Top Value`, `Mid Value`, `Dormant`, `Low Spend`).

### 2.3 `dim_products.csv`
- **Grain**: 1 row per product SKU (32,951 rows).
- **Columns**: `product_id`, `product_category_name_english`, `category_group`, `assumed_cogs_rate`, `assumed_gross_margin_rate`.

### 2.4 `fact_order_items.csv`
- **Grain**: 1 row per ordered item line (112,650 rows).
- **Columns**: `order_id`, `order_item_id`, `product_id`, `seller_id`, `price`, `freight_value`, `assumed_cogs_brl`, `assumed_gross_profit_brl`.
- **Enriched Attributes**:
  - `assumed_cogs_brl`: Assumed Cost of Goods Sold `price * assumed_cogs_rate` (*assumed margin, not real data*).
  - `assumed_gross_profit_brl`: Assumed gross margin contribution `price * assumed_gross_margin_rate` (*assumed margin, not real data*).

### 2.5 `dim_calendar.csv`
- **Grain**: 1 row per calendar day (1,096 rows covering 2016-01-01 to 2018-12-31).
- **Columns**: `date_key`, `Date`, `Year`, `Quarter`, `QuarterName`, `Month`, `MonthName`, `MonthShort`, `YearMonth`, `YearMonthInt`, `WeekNumber`, `DayOfWeek`, `DayName`, `IsWeekend`.

---

## 3. Financial & Benchmark Margin Assumptions (`config/margin_assumptions.yaml`)

> **Notice**: The raw Olist dataset contains zero supplier invoice or wholesale acquisition cost data. The COGS rates below represent retail industry benchmark assumptions established to enable unit-economic modeling (*assumed margin, not real data*).

| Macro Category Group | Assumed COGS Rate (%) | Assumed Gross Margin (%) | Typical Product Categories Included |
| :--- | :---: | :---: | :--- |
| **Beauty & Personal Care** | 50.00% | 50.00% | Perfumery, health beauty, baby hygiene |
| **Fashion & Apparel** | 45.00% | 55.00% | Watches, gifts, fashion shoes, luggage |
| **Food, Drinks & Flowers** | 55.00% | 45.00% | Food, gourmet drinks, flowers |
| **Furniture & Home Decor** | 60.00% | 40.00% | Bed bath table, housewares, furniture office |
| **Sports, Toys & Hobbies** | 55.00% | 45.00% | Sports leisure, toys, musical instruments |
| **Computers & Electronics** | 75.00% | 25.00% | Computers accessories, telephony, electronics |
| **Home Appliances** | 70.00% | 30.00% | Home appliances, small appliances |
| **Tools & Construction** | 60.00% | 40.00% | Construction tools, garden tools |
| **Automotive & Parts** | 65.00% | 35.00% | Auto parts, motorcycle accessories |
| **Books & Media** | 40.00% | 60.00% | Books technical, general interest, audio CDs |
| **Commercial & General** | 60.00% | 40.00% | Agro industry, stationery, other categories |

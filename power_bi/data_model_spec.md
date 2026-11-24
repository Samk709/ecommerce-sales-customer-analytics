# Power BI Data Model Specification (Star Schema)

## 1. Executive Summary & Architecture Overview

The **E-Commerce Sales & Customer Intelligence Platform** data model is architected as an **enterprise Kimball-style Star Schema** optimized for high-performance analytical querying in Power BI Desktop (VertiPaq in-memory engine).

By decoupling dimensional entities (`dim_orders`, `dim_customers`, `dim_products`, `dim_sellers`, `dim_calendar`) from transactional fact tables (`fact_order_items`, `fact_order_payments`, `fact_order_reviews`), this schema eliminates circular dependencies, avoids bidirectional filtering pitfalls, and guarantees blazing-fast DAX measure evaluation.

> **Storage Mode**: **Import Mode** across all tables (optimized columnar compression).
> **Currency Standard**: **Brazilian Reais (R$ / BRL)**.
> **Date Master**: `dim_calendar` acts as the single source of truth for all time intelligence.

---

## 2. Star Schema Entity-Relationship Diagram

```mermaid
erDiagram
    dim_calendar ||--o{ dim_orders : "order_purchase_date (Active 1:N)"
    dim_calendar ||--o{ dim_orders : "order_delivered_customer_date_only (Inactive 1:N)"
    dim_calendar ||--o{ dim_orders : "order_estimated_delivery_date_only (Inactive 1:N)"
    dim_customers ||--o{ dim_orders : "customer_id (1:N)"
    dim_orders ||--|{ fact_order_items : "order_id (1:N)"
    dim_orders ||--|{ fact_order_payments : "order_id (1:N)"
    dim_orders ||--o{ fact_order_reviews : "order_id (1:N)"
    dim_products ||--o{ fact_order_items : "product_id (1:N)"
    dim_sellers ||--o{ fact_order_items : "seller_id (1:N)"

    dim_calendar {
        date Date PK "Calendar date (YYYY-MM-DD)"
        int Year "Calendar Year (2016-2018)"
        varchar QuarterName "Quarter (Q1 - Q4)"
        int Month "Month number (1-12)"
        varchar MonthName "Full month name (e.g. November)"
        varchar YearMonth "Year-Month (YYYY-MM)"
        int YearMonthInt "Sorting key (e.g. 201711)"
        int DayOfWeek "Day of week (1=Mon, 7=Sun)"
        varchar DayName "Day name (e.g. Monday)"
        int IsWeekend "Flag (1=Weekend, 0=Weekday)"
    }

    dim_customers {
        varchar customer_id PK "Order-session customer identifier"
        varchar customer_unique_id "Real individual customer identifier"
        varchar customer_state "2-letter state code"
        varchar rfm_segment "Top Value, Mid Value, Dormant, Low Spend"
        int is_repeat_customer "Flag (1=Repeat buyer >=2 orders, 0=Single)"
    }

    dim_orders {
        varchar order_id PK "Unique order identifier"
        varchar customer_id FK "References dim_customers"
        varchar order_status "delivered, shipped, canceled, etc."
        date order_purchase_date FK "Active FK to dim_calendar[Date]"
        date order_delivered_customer_date_only FK "Inactive FK to dim_calendar[Date]"
        date order_estimated_delivery_date_only FK "Inactive FK to dim_calendar[Date]"
        int delivery_delay_days "Calendar day difference (Delivered - Estimated)"
        int is_delayed "1 if late, 0 if on-time/early"
        decimal delivery_lead_time_days "Total lead time in decimal days"
        decimal carrier_transit_time_days "Carrier transit time in decimal days"
    }

    dim_products {
        varchar product_id PK "Unique product SKU identifier"
        varchar product_category_name_english "Clean English category name"
        varchar category_group "11 macro groups (e.g. Computers & Electronics)"
        decimal assumed_cogs_rate "Benchmark COGS rate (assumed, not real data)"
        decimal assumed_gross_margin_rate "Benchmark gross margin rate"
    }

    dim_sellers {
        varchar seller_id PK "Unique seller merchant ID"
        int seller_zip_code_prefix "5-digit postal code"
        varchar seller_city "Seller City"
        varchar seller_state "Seller State (2-letter code)"
    }

    fact_order_items {
        varchar order_id FK "References dim_orders"
        int order_item_id "Line-item sequence (1, 2, ...)"
        varchar product_id FK "References dim_products"
        varchar seller_id FK "References dim_sellers"
        decimal price "Item price in BRL (R$)"
        decimal freight_value "Item freight charge in BRL (R$)"
        decimal assumed_cogs_brl "Item COGS in BRL (price * cogs_rate)"
        decimal assumed_gross_profit_brl "Item gross profit in BRL (price * margin_rate)"
    }

    fact_order_payments {
        varchar order_id FK "References dim_orders"
        int payment_sequential "Payment sequence number"
        varchar payment_type "credit_card, boleto, voucher, debit_card"
        int payment_installments "Number of installments"
        decimal payment_value "Payment amount in BRL (R$)"
    }

    fact_order_reviews {
        varchar review_id "Survey response ID"
        varchar order_id FK "References dim_orders"
        int review_score "CSAT rating (1 to 5 stars)"
    }
```

---

## 3. Data Dictionary & Table Inventory

| Table Name | Type | Granularity | Exact Rows | Primary Key | Description |
|:---|:---|:---|---:|:---|:---|
| **`dim_calendar`** | Dimension | 1 day | 1,096 | `Date` | Standard date master (2016-01-01 to 2018-12-31) |
| **`dim_orders`** | Dimension | 1 order | 99,441 | `order_id` | Order headers enriched with fulfillment SLA metrics |
| **`dim_customers`** | Dimension | 1 customer order key | 99,441 | `customer_id` | Customers enriched with RFM value segments |
| **`dim_products`** | Dimension | 1 product SKU | 32,951 | `product_id` | Product catalog with 11 macro categories & assumed margin rates |
| **`dim_sellers`** | Dimension | 1 merchant | 3,095 | `seller_id` | Merchant directory with geographical locations |
| **`fact_order_items`** | Fact | 1 order line item | 112,650 | Composite (`order_id`, `order_item_id`) | Sales merchandise revenue, freight, COGS, and GP |
| **`fact_order_payments`** | Fact | 1 payment transaction | 103,886 | Composite (`order_id`, `payment_sequential`) | Transaction amounts, payment methods, and installments |
| **`fact_order_reviews`** | Fact | 1 survey review | 99,224 | `review_id` / `order_id` | Customer CSAT survey ratings and response timestamps |

---

## 4. Relationship Cardinality & Cross-Filtering Configuration

All relationships in this data model follow strict **One-to-Many (`1:*`)** cardinality with **Single Cross-Filter Direction** flowing from Dimensions down to Fact tables:

| From Table (Dimension) | From Column (PK) | To Table (Fact / Dim) | To Column (FK) | Cardinality | Cross-Filter | Relationship State |
|:---|:---|:---|:---|:---:|:---:|:---:|
| `dim_calendar` | `Date` | `dim_orders` | `order_purchase_date` | `1:*` | Single (`dim_calendar` $\rightarrow$ `dim_orders`) | **Active** |
| `dim_calendar` | `Date` | `dim_orders` | `order_delivered_customer_date_only` | `1:*` | Single (`dim_calendar` $\rightarrow$ `dim_orders`) | **Inactive** *(Use via `USERELATIONSHIP` in DAX)* |
| `dim_calendar` | `Date` | `dim_orders` | `order_estimated_delivery_date_only` | `1:*` | Single (`dim_calendar` $\rightarrow$ `dim_orders`) | **Inactive** *(Use via `USERELATIONSHIP` in DAX)* |
| `dim_customers` | `customer_id` | `dim_orders` | `customer_id` | `1:*` | Single (`dim_customers` $\rightarrow$ `dim_orders`) | **Active** |
| `dim_orders` | `order_id` | `fact_order_items` | `order_id` | `1:*` | Single (`dim_orders` $\rightarrow$ `fact_order_items`) | **Active** |
| `dim_orders` | `order_id` | `fact_order_payments` | `order_id` | `1:*` | Single (`dim_orders` $\rightarrow$ `fact_order_payments`) | **Active** |
| `dim_orders` | `order_id` | `fact_order_reviews` | `order_id` | `1:*` | Single (`dim_orders` $\rightarrow$ `fact_order_reviews`) | **Active** |
| `dim_products` | `product_id` | `fact_order_items` | `product_id` | `1:*` | Single (`dim_products` $\rightarrow$ `fact_order_items`) | **Active** |
| `dim_sellers` | `seller_id` | `fact_order_items` | `seller_id` | `1:*` | Single (`dim_sellers` $\rightarrow$ `fact_order_items`) | **Active** |

---

## 5. Modeling Best Practices & Enterprise Standards

1. **Strict Star Schema Topology**:
   - Fact tables never filter other fact tables directly.
   - Slicing and filtering are executed through dimension tables (`dim_calendar`, `dim_products`, `dim_customers`, `dim_sellers`, `dim_orders`).
2. **Role-Playing Date Relationships**:
   - The primary active relationship between `dim_calendar[Date]` and `dim_orders[order_purchase_date]` ensures standard sales time intelligence (e.g. Month-over-Month, YTD).
   - Inactive relationships are leveraged via DAX `USERELATIONSHIP(dim_calendar[Date], dim_orders[order_delivered_customer_date_only])` when analyzing delivery fulfillment volume by delivery month.
3. **Dedicated Measures Table**:
   - All DAX measures are consolidated in a disconnected, empty table named `_Measures` organized into numbered display folders for clean report authoring.
4. **Column Formatting**:
   - All currency fields are formatted as `R$ #,##0.00; -R$ #,##0.00; "R$ 0.00"`.
   - Percentage fields are formatted as `0.00%`.
   - Integer counts are formatted as `#,##0`.

# Entity-Relationship (ER) Diagram & Relational Schema Design

This document details the relational data architecture designed for the **Olist Brazilian E-Commerce Analytics Platform**.

---

## 1. Relational ER Diagram

```mermaid
erDiagram
    dim_customers ||--o{ dim_orders : "places (1:N)"
    dim_orders ||--|{ fact_order_items : "contains (1:N)"
    dim_orders ||--|{ fact_order_payments : "paid_via (1:N)"
    dim_orders ||--o{ fact_order_reviews : "rated_by (1:N)"
    dim_products ||--o{ fact_order_items : "included_in (1:N)"
    dim_sellers ||--o{ fact_order_items : "fulfilled_by (1:N)"
    dim_category_translation ||--o{ dim_products : "translates (1:N)"
    dim_geolocation ||--o{ dim_customers : "locates_customer (1:N, left join)"
    dim_geolocation ||--o{ dim_sellers : "locates_seller (1:N, left join)"

    dim_customers {
        varchar customer_id PK "Unique identifier per order-session"
        varchar customer_unique_id "Real-world individual customer identifier"
        int customer_zip_code_prefix "5-digit postal code"
        varchar customer_city "City name (Title Case)"
        varchar customer_state "2-letter uppercase state code"
    }

    dim_orders {
        varchar order_id PK "Unique order identifier"
        varchar customer_id FK "References dim_customers"
        varchar order_status "delivered, shipped, canceled, etc."
        datetime order_purchase_timestamp "Initial order timestamp"
        datetime order_approved_at "Payment approval timestamp"
        datetime order_delivered_carrier_date "Carrier handover timestamp"
        datetime order_delivered_customer_date "Actual delivery timestamp"
        datetime order_estimated_delivery_date "Promised SLA delivery date"
    }

    fact_order_items {
        varchar order_id PK,FK "References dim_orders"
        int order_item_id PK "Sequential line-item sequence (1, 2, ...)"
        varchar product_id FK "References dim_products"
        varchar seller_id FK "References dim_sellers"
        datetime shipping_limit_date "Seller dispatch deadline"
        decimal price "Item sales price in BRL (R$)"
        decimal freight_value "Item freight charge in BRL (R$)"
    }

    fact_order_payments {
        varchar order_id PK,FK "References dim_orders"
        int payment_sequential PK "Payment sequence number (1, 2, ...)"
        varchar payment_type "credit_card, boleto, voucher, debit_card"
        int payment_installments "Number of credit installments"
        decimal payment_value "Transaction amount in BRL (R$)"
    }

    fact_order_reviews {
        int review_surrogate_id PK "Unique surrogate row identifier"
        varchar review_id "Original survey response ID"
        varchar order_id FK "References dim_orders"
        tinyint review_score "CSAT score from 1 (poor) to 5 (excellent)"
        varchar review_comment_title "Cleaned review title text"
        text review_comment_message "Cleaned review comment feedback"
        datetime review_creation_date "Survey sent date"
        datetime review_answer_timestamp "Survey response timestamp"
    }

    dim_products {
        varchar product_id PK "Unique product SKU identifier"
        varchar product_category_name "Original Portuguese category name"
        int product_name_lenght "Title length in characters"
        int product_description_lenght "Description character count"
        int product_photos_qty "Photo count on listing"
        decimal product_weight_g "Physical weight in grams"
        decimal product_length_cm "Package length in cm"
        decimal product_height_cm "Package height in cm"
        decimal product_width_cm "Package width in cm"
        varchar product_category_name_english "English translated category"
        varchar category_group "Macro sector (e.g. Computers & Electronics)"
        decimal assumed_cogs_rate "Benchmark COGS rate (assumption, not real data)"
        decimal assumed_gross_margin_rate "Benchmark gross margin rate"
    }

    dim_sellers {
        varchar seller_id PK "Unique seller merchant ID"
        int seller_zip_code_prefix "5-digit seller zip code"
        varchar seller_city "Seller city name"
        varchar seller_state "Seller state code"
    }

    dim_geolocation {
        int geolocation_zip_code_prefix PK "Deduplicated 5-digit zip prefix"
        decimal geolocation_lat "Median latitude coordinate"
        decimal geolocation_lng "Median longitude coordinate"
        varchar geolocation_city "Modal city name"
        varchar geolocation_state "Modal state code"
    }

    dim_category_translation {
        varchar product_category_name PK "Portuguese category name"
        varchar product_category_name_english "English translation"
    }
```

---

## 2. Schema Architecture & Design Justification

1. **Star / Snowflake Hybrid Schema**:
   * **Central Facts**: Transaction items (`fact_order_items`), installment settlements (`fact_order_payments`), and survey feedback (`fact_order_reviews`).
   * **Conformed Dimensions**: Orders header (`dim_orders`), Customers (`dim_customers`), Sellers (`dim_sellers`), Products (`dim_products`), and Postal Geography (`dim_geolocation`).
2. **Grain Specification**:
   * `fact_order_items`: One row per item SKU per order. Composite Primary Key: `(order_id, order_item_id)`.
   * `fact_order_payments`: One row per payment split per order. Composite Primary Key: `(order_id, payment_sequential)`.
   * `fact_order_reviews`: One row per customer feedback submission. Surrogate Primary Key: `review_surrogate_id`.
3. **Data Integrity & Referential Constraints**:
   * All child tables enforce `FOREIGN KEY ... ON DELETE RESTRICT ON UPDATE CASCADE` to prevent orphaned transactions.
   * All monetary attributes are typed as `DECIMAL(10, 2)` to eliminate floating-point arithmetic rounding errors common with `FLOAT` or `DOUBLE`.

-- ==============================================================================
-- DDL TABLE CREATION SCRIPT: Olist Relational Schema
-- ==============================================================================
-- Normalized Star / Snowflake Schema for E-Commerce Sales & Intelligence
-- Currency Note: All monetary amounts (price, freight_value, payment_value) are in BRL (R$).
-- ==============================================================================

USE olist_ecommerce;

-- Drop dependent tables first to avoid foreign key violation on re-run
DROP TABLE IF EXISTS fact_order_reviews;
DROP TABLE IF EXISTS fact_order_payments;
DROP TABLE IF EXISTS fact_order_items;
DROP TABLE IF EXISTS dim_orders;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_sellers;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_geolocation;
DROP TABLE IF EXISTS dim_category_translation;

-- ------------------------------------------------------------------------------
-- 1. Dimension: Category Translations (Portuguese to English lookup)
-- ------------------------------------------------------------------------------
CREATE TABLE dim_category_translation (
    product_category_name VARCHAR(100) NOT NULL,
    product_category_name_english VARCHAR(100) NOT NULL,
    PRIMARY KEY (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Master translation mapping from Portuguese to English category names';

-- ------------------------------------------------------------------------------
-- 2. Dimension: Geolocation Reference (Aggregated by unique zip prefix)
-- ------------------------------------------------------------------------------
CREATE TABLE dim_geolocation (
    geolocation_zip_code_prefix INT NOT NULL,
    geolocation_lat DECIMAL(10, 6) NOT NULL,
    geolocation_lng DECIMAL(10, 6) NOT NULL,
    geolocation_city VARCHAR(100) NOT NULL,
    geolocation_state VARCHAR(2) NOT NULL,
    PRIMARY KEY (geolocation_zip_code_prefix)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Deduplicated postal geographic coordinates with median lat/lng in Brazil';

-- ------------------------------------------------------------------------------
-- 3. Dimension: Customers
-- ------------------------------------------------------------------------------
CREATE TABLE dim_customers (
    customer_id VARCHAR(32) NOT NULL,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INT NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    customer_state VARCHAR(2) NOT NULL,
    PRIMARY KEY (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Customer directory: customer_unique_id tracks returning people across customer_ids';

-- ------------------------------------------------------------------------------
-- 4. Dimension: Sellers
-- ------------------------------------------------------------------------------
CREATE TABLE dim_sellers (
    seller_id VARCHAR(32) NOT NULL,
    seller_zip_code_prefix INT NOT NULL,
    seller_city VARCHAR(100) NOT NULL,
    seller_state VARCHAR(2) NOT NULL,
    PRIMARY KEY (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Marketplace merchants and fulfillment partner directory';

-- ------------------------------------------------------------------------------
-- 5. Dimension: Products (Enhanced with Financial Assumptions)
-- ------------------------------------------------------------------------------
CREATE TABLE dim_products (
    product_id VARCHAR(32) NOT NULL,
    product_category_name VARCHAR(100) NOT NULL,
    product_name_lenght INT NULL,
    product_description_lenght INT NULL,
    product_photos_qty INT NULL,
    product_weight_g DECIMAL(10, 2) NULL,
    product_length_cm DECIMAL(10, 2) NULL,
    product_height_cm DECIMAL(10, 2) NULL,
    product_width_cm DECIMAL(10, 2) NULL,
    product_category_name_english VARCHAR(100) NOT NULL,
    category_group VARCHAR(100) NOT NULL,
    assumed_cogs_rate DECIMAL(5, 4) NOT NULL COMMENT 'Assumed Cost of Goods Sold % (assumption, not real data)',
    assumed_gross_margin_rate DECIMAL(5, 4) NOT NULL COMMENT 'Assumed Gross Margin % (assumption, not real data)',
    PRIMARY KEY (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Product catalog enriched with category grouping and COGS margin benchmarks';

-- ------------------------------------------------------------------------------
-- 6. Dimension: Orders (Central transaction lifecycle entity)
-- ------------------------------------------------------------------------------
CREATE TABLE dim_orders (
    order_id VARCHAR(32) NOT NULL,
    customer_id VARCHAR(32) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    order_purchase_timestamp DATETIME NOT NULL,
    order_approved_at DATETIME NULL,
    order_delivered_carrier_date DATETIME NULL,
    order_delivered_customer_date DATETIME NULL,
    order_estimated_delivery_date DATETIME NOT NULL,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Order transaction header tracking lifecycle milestone timestamps';

-- ------------------------------------------------------------------------------
-- 7. Fact: Order Items (Line-item grain)
-- ------------------------------------------------------------------------------
CREATE TABLE fact_order_items (
    order_id VARCHAR(32) NOT NULL,
    order_item_id INT NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    seller_id VARCHAR(32) NOT NULL,
    shipping_limit_date DATETIME NOT NULL,
    price DECIMAL(10, 2) NOT NULL COMMENT 'Item sales price in BRL (R$)',
    freight_value DECIMAL(10, 2) NOT NULL COMMENT 'Shipping freight charge in BRL (R$)',
    PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_items_order
        FOREIGN KEY (order_id) REFERENCES dim_orders (order_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_items_product
        FOREIGN KEY (product_id) REFERENCES dim_products (product_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_items_seller
        FOREIGN KEY (seller_id) REFERENCES dim_sellers (seller_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Line-item transaction fact table with item price and freight';

-- ------------------------------------------------------------------------------
-- 8. Fact: Order Payments
-- ------------------------------------------------------------------------------
CREATE TABLE fact_order_payments (
    order_id VARCHAR(32) NOT NULL,
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(30) NOT NULL,
    payment_installments INT NOT NULL,
    payment_value DECIMAL(10, 2) NOT NULL COMMENT 'Payment installment value in BRL (R$)',
    PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id) REFERENCES dim_orders (order_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Payment settlement method, installments, and payment amounts';

-- ------------------------------------------------------------------------------
-- 9. Fact: Order Reviews
-- ------------------------------------------------------------------------------
CREATE TABLE fact_order_reviews (
    review_surrogate_id INT NOT NULL,
    review_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    review_score TINYINT NOT NULL COMMENT 'CSAT rating score between 1 and 5',
    review_comment_title VARCHAR(255) NULL,
    review_comment_message TEXT NULL,
    review_creation_date DATETIME NOT NULL,
    review_answer_timestamp DATETIME NOT NULL,
    PRIMARY KEY (review_surrogate_id),
    CONSTRAINT fk_reviews_order
        FOREIGN KEY (order_id) REFERENCES dim_orders (order_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Customer satisfaction survey review ratings and feedback';

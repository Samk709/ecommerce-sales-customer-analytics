-- ==============================================================================
-- STRATEGIC INDEXING SCRIPT: Olist Analytics Warehouse
-- ==============================================================================
-- Database Engine: InnoDB (B-Tree Indexes)
-- Purpose: Optimize analytical query performance across joins, aggregations,
--          window functions, and customer segmentation filters.
-- ==============================================================================

USE olist_ecommerce;

-- ------------------------------------------------------------------------------
-- 1. Orders Indexes
-- ------------------------------------------------------------------------------
-- Why: Frequently queried in every sales report for time-series filtering (e.g. BETWEEN dates),
--      monthly cohort grouping, and MoM trend calculations.
CREATE INDEX idx_orders_purchase_timestamp 
    ON dim_orders (order_purchase_timestamp);

-- Why: Accelerates filtering for valid fulfilled orders ('delivered') vs cancelled/in-transit orders.
CREATE INDEX idx_orders_status 
    ON dim_orders (order_status);

-- Why: Required for fast 1-to-many joins between customers and their orders.
CREATE INDEX idx_orders_customer_id 
    ON dim_orders (customer_id);

-- ------------------------------------------------------------------------------
-- 2. Customers Indexes
-- ------------------------------------------------------------------------------
-- Why: Critical for RFM segmentation, customer lifetime value (CLV), and cohort retention.
--      In Olist, 'customer_id' is transaction-scoped, while 'customer_unique_id' identifies
--      the real human customer across multiple orders.
CREATE INDEX idx_customers_unique_id 
    ON dim_customers (customer_unique_id);

-- Why: Accelerates regional grouping and geographical lookups.
CREATE INDEX idx_customers_state_city 
    ON dim_customers (customer_state, customer_city);

CREATE INDEX idx_customers_zip 
    ON dim_customers (customer_zip_code_prefix);

-- ------------------------------------------------------------------------------
-- 3. Order Items Indexes
-- ------------------------------------------------------------------------------
-- Why: Highly frequent join column for product-level sales, category rollups, and Pareto 80/20 analysis.
CREATE INDEX idx_order_items_product_id 
    ON fact_order_items (product_id);

-- Why: Accelerates seller volume, vendor fulfillment latency, and merchant rating queries.
CREATE INDEX idx_order_items_seller_id 
    ON fact_order_items (seller_id);

-- ------------------------------------------------------------------------------
-- 4. Products Indexes
-- ------------------------------------------------------------------------------
-- Why: Filters and groups by macro sector (e.g. 'Computers & Electronics') for unit economics.
CREATE INDEX idx_products_category_group 
    ON dim_products (category_group);

-- Why: Facilitates category-level breakdown and translation queries.
CREATE INDEX idx_products_english_cat 
    ON dim_products (product_category_name_english);

-- ------------------------------------------------------------------------------
-- 5. Order Payments Indexes
-- ------------------------------------------------------------------------------
-- Why: Speeds up financial breakdown by payment method (credit card, boleto, voucher) and installment volume.
CREATE INDEX idx_payments_type 
    ON fact_order_payments (payment_type);

-- ------------------------------------------------------------------------------
-- 6. Order Reviews Indexes
-- ------------------------------------------------------------------------------
-- Why: Essential for correlating delivery logistics latency (actual vs estimated delivery) with review score.
CREATE INDEX idx_reviews_order_id 
    ON fact_order_reviews (order_id);

-- Why: Accelerates filtering for detractors (scores 1-2) vs promoters (score 5) in CSAT analysis.
CREATE INDEX idx_reviews_score 
    ON fact_order_reviews (review_score);

-- ------------------------------------------------------------------------------
-- 7. Sellers & Geolocation Indexes
-- ------------------------------------------------------------------------------
CREATE INDEX idx_sellers_state_city 
    ON dim_sellers (seller_state, seller_city);

CREATE INDEX idx_sellers_zip 
    ON dim_sellers (seller_zip_code_prefix);

CREATE INDEX idx_geolocation_state_city 
    ON dim_geolocation (geolocation_state, geolocation_city);

-- ==============================================================================
-- Query 6: Top 10 Product Categories by Item Sales Revenue
-- Tier: 2 | Question: Which 10 product categories generate the highest merchandise sales revenue (excluding freight), and what percentage of total marketplace GMV do they represent?
-- Filter: Includes only completed orders (order_status = 'delivered'). Revenue strictly reflects product item price, excluding freight.
-- ==============================================================================
SELECT 
    p.product_category_name_english AS category,
    p.category_group,
    COUNT(i.order_item_id) AS units_sold,
    ROUND(SUM(i.price), 2) AS item_revenue_brl,
    ROUND(SUM(i.price) * 100.0 / (
        SELECT SUM(i2.price) 
        FROM fact_order_items i2 
        JOIN dim_orders o2 ON i2.order_id = o2.order_id 
        WHERE o2.order_status = 'delivered'
    ), 2) AS revenue_share_pct
FROM fact_order_items i
JOIN dim_orders o ON i.order_id = o.order_id
JOIN dim_products p ON i.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY p.product_category_name_english, p.category_group
ORDER BY item_revenue_brl DESC
LIMIT 10;;

-- ==============================================================================
-- Query 7: Top 10 Customer States by Revenue and Average Spend
-- Tier: 2 | Question: Which Brazilian states dominate marketplace demand, and how does item spend per order compare across regions?
-- Filter: Includes only completed orders (order_status = 'delivered'). Item revenue excludes freight; freight is broken out as a distinct column.
-- ==============================================================================
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS delivered_orders,
    COUNT(i.order_item_id) AS total_items,
    ROUND(SUM(i.price), 2) AS total_item_revenue_brl,
    ROUND(SUM(i.freight_value), 2) AS total_freight_brl,
    ROUND(SUM(i.price) / COUNT(DISTINCT o.order_id), 2) AS avg_item_spend_per_order_brl
FROM dim_orders o
JOIN dim_customers c ON o.customer_id = c.customer_id
JOIN fact_order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_item_revenue_brl DESC
LIMIT 10;;

-- ==============================================================================
-- Query 8: Delivery Delay Impact on Customer Satisfaction (CSAT)
-- Tier: 2 | Question: How severely does late delivery past the promised estimated date degrade customer satisfaction ratings and inflate 1-star reviews?
-- Filter: Includes only completed orders (order_status = 'delivered') with non-null customer delivery timestamps.
-- ==============================================================================
SELECT 
    CASE 
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On-Time / Early'
        ELSE 'Delayed / Late'
    END AS delivery_performance,
    COUNT(r.review_surrogate_id) AS review_count,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    ROUND(SUM(CASE WHEN r.review_score IN (1, 2) THEN 1 ELSE 0 END) * 100.0 / COUNT(r.review_surrogate_id), 2) AS detractor_pct_1_2_star,
    ROUND(SUM(CASE WHEN r.review_score = 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(r.review_surrogate_id), 2) AS promoter_pct_5_star
FROM dim_orders o
JOIN fact_order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' 
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY delivery_performance;;

-- ==============================================================================
-- Query 9: Freight Burden by Macro Category Group
-- Tier: 2 | Question: What is the freight-to-price ratio across our 11 macro category groups, and which sectors suffer from high logistics drag?
-- Filter: Includes only completed orders (order_status = 'delivered'). Compares total shipping freight against total product price.
-- ==============================================================================
SELECT 
    p.category_group,
    COUNT(i.order_item_id) AS items_sold,
    ROUND(SUM(i.price), 2) AS total_item_revenue_brl,
    ROUND(SUM(i.freight_value), 2) AS total_freight_brl,
    ROUND(SUM(i.freight_value) * 100.0 / SUM(i.price), 2) AS freight_to_price_ratio_pct,
    ROUND(AVG(i.freight_value), 2) AS avg_freight_per_item_brl
FROM fact_order_items i
JOIN dim_orders o ON i.order_id = o.order_id
JOIN dim_products p ON i.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY p.category_group
ORDER BY freight_to_price_ratio_pct DESC;;

-- ==============================================================================
-- Query 10: Top 10 Sellers by Revenue and Average Fulfillment Dispatch Speed
-- Tier: 2 | Question: Who are the top 10 marketplace sellers by sales volume, and how rapidly do they dispatch orders to the carrier?
-- Filter: Includes only completed orders (order_status = 'delivered') with non-null carrier handover dates. Revenue excludes freight.
-- ==============================================================================
SELECT 
    s.seller_id,
    s.seller_state,
    COUNT(DISTINCT o.order_id) AS completed_orders,
    COUNT(i.order_item_id) AS items_sold,
    ROUND(SUM(i.price), 2) AS total_item_revenue_brl,
    ROUND(AVG(TIMESTAMPDIFF(HOUR, o.order_purchase_timestamp, o.order_delivered_carrier_date)), 1) AS avg_dispatch_hours
FROM fact_order_items i
JOIN dim_orders o ON i.order_id = o.order_id
JOIN dim_sellers s ON i.seller_id = s.seller_id
WHERE o.order_status = 'delivered' 
  AND o.order_delivered_carrier_date IS NOT NULL
GROUP BY s.seller_id, s.seller_state
ORDER BY total_item_revenue_brl DESC
LIMIT 10;;


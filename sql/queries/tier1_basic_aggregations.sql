-- ==============================================================================
-- Query 1: Total Revenue & Volume KPI Overview
-- Tier: 1 | Question: What is the total item revenue (excluding freight), total shipping freight, gross merchandise value (GMV), total delivered orders, and total items sold across the platform?
-- Filter: Includes only completed orders (order_status = 'delivered'). Item revenue excludes freight; GMV includes freight.
-- ==============================================================================
SELECT 
    COUNT(DISTINCT o.order_id) AS total_delivered_orders,
    COUNT(i.order_item_id) AS total_items_sold,
    ROUND(SUM(i.price), 2) AS item_revenue_brl,
    ROUND(SUM(i.freight_value), 2) AS total_freight_brl,
    ROUND(SUM(i.price + i.freight_value), 2) AS gross_merchandise_value_brl,
    ROUND(AVG(i.price), 2) AS avg_item_price_brl
FROM dim_orders o
JOIN fact_order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered';;

-- ==============================================================================
-- Query 2: Average Order Value (AOV) & Basket Depth
-- Tier: 1 | Question: What is the Average Order Value (AOV) excluding and including freight, and what is the average item count per delivered order?
-- Filter: Includes only completed orders (order_status = 'delivered'). Distinguishes item revenue AOV from total customer checkout AOV.
-- ==============================================================================
SELECT 
    ROUND(SUM(i.price) / COUNT(DISTINCT o.order_id), 2) AS aov_item_revenue_brl,
    ROUND(SUM(i.price + i.freight_value) / COUNT(DISTINCT o.order_id), 2) AS aov_with_freight_brl,
    ROUND(COUNT(i.order_item_id) / COUNT(DISTINCT o.order_id), 2) AS avg_items_per_order
FROM dim_orders o
JOIN fact_order_items i ON o.order_id = i.order_id
WHERE o.order_status = 'delivered';;

-- ==============================================================================
-- Query 3: Order Status Distribution & Platform Cancellation Rate
-- Tier: 1 | Question: What is the distribution of orders across all operational lifecycle statuses, and what percentage of total orders are canceled or unavailable?
-- Filter: Evaluates all 99,441 orders in the warehouse without filtering, in order to measure operational fulfillment and drop-off rates.
-- ==============================================================================
SELECT 
    order_status,
    COUNT(order_id) AS order_count,
    ROUND(COUNT(order_id) * 100.0 / SUM(COUNT(order_id)) OVER(), 2) AS percentage_of_total
FROM dim_orders
GROUP BY order_status
ORDER BY order_count DESC;;

-- ==============================================================================
-- Query 4: Payment Method Breakdown & Installment Usage
-- Tier: 1 | Question: How do Brazilian customers pay on the platform, and which payment methods drive the highest volume, revenue, and installment financing?
-- Filter: Includes payments linked to delivered orders (order_status = 'delivered'). Values reflect total settled transaction amounts in BRL.
-- ==============================================================================
SELECT 
    p.payment_type,
    COUNT(p.payment_sequential) AS transaction_count,
    ROUND(COUNT(p.payment_sequential) * 100.0 / SUM(COUNT(p.payment_sequential)) OVER(), 2) AS transaction_share_pct,
    ROUND(SUM(p.payment_value), 2) AS total_payment_value_brl,
    ROUND(AVG(p.payment_value), 2) AS avg_payment_value_brl,
    ROUND(AVG(p.payment_installments), 1) AS avg_installments
FROM fact_order_payments p
JOIN dim_orders o ON p.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.payment_type
ORDER BY total_payment_value_brl DESC;;

-- ==============================================================================
-- Query 5: Customer Satisfaction (CSAT) Rating Distribution
-- Tier: 1 | Question: What is the overall rating distribution (1 to 5 stars) from customer survey feedback on delivered orders, and what is the platform's average CSAT score?
-- Filter: Includes reviews associated with delivered orders (order_status = 'delivered').
-- ==============================================================================
SELECT 
    r.review_score,
    COUNT(r.review_surrogate_id) AS total_reviews,
    ROUND(COUNT(r.review_surrogate_id) * 100.0 / SUM(COUNT(r.review_surrogate_id)) OVER(), 2) AS percentage_of_reviews
FROM fact_order_reviews r
JOIN dim_orders o ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY r.review_score
ORDER BY r.review_score DESC;;


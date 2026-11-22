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
-- Filter: Includes only completed orders (order_status = 'delivered') with non-null customer delivery timestamps. Uses calendar date comparison (DATE(delivered) <= DATE(estimated)) to avoid time-of-day bias against estimated dates lacking timestamps.
-- ==============================================================================
SELECT 
    CASE 
        WHEN DATE(o.order_delivered_customer_date) <= DATE(o.order_estimated_delivery_date) THEN 'On-Time / Early'
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

-- ==============================================================================
-- Query 11: Repeat vs. One-Time Customer Analysis
-- Tier: 3 | Question: What proportion of customers are repeat buyers (>=2 orders) versus one-time buyers, and what percentage of total platform revenue do they generate?
-- Filter: Includes only completed orders (order_status = 'delivered'). Revenue excludes freight. Tracks real humans via customer_unique_id.
-- ==============================================================================
WITH customer_orders AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(i.price) AS total_spend_brl
    FROM dim_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_segments AS (
    SELECT 
        CASE WHEN order_count > 1 THEN 'Repeat Customer (>= 2 Orders)' ELSE 'One-Time Customer (1 Order)' END AS customer_type,
        customer_unique_id,
        order_count,
        total_spend_brl
    FROM customer_orders
)
SELECT 
    customer_type,
    COUNT(customer_unique_id) AS customer_count,
    ROUND(COUNT(customer_unique_id) * 100.0 / (SELECT COUNT(*) FROM customer_segments), 2) AS customer_pct,
    ROUND(SUM(total_spend_brl), 2) AS total_revenue_brl,
    ROUND(SUM(total_spend_brl) * 100.0 / (SELECT SUM(total_spend_brl) FROM customer_segments), 2) AS revenue_pct,
    ROUND(AVG(total_spend_brl), 2) AS avg_spend_per_customer_brl
FROM customer_segments
GROUP BY customer_type;;

-- ==============================================================================
-- Query 12: Multi-Item Basket Penetration & Volume
-- Tier: 3 | Question: How many orders contain single items versus multiple items, and how much revenue does multi-item ordering generate?
-- Filter: Includes only completed orders (order_status = 'delivered'). Revenue strictly reflects product prices, excluding freight.
-- ==============================================================================
WITH order_basket AS (
    SELECT 
        order_id,
        COUNT(order_item_id) AS item_count,
        SUM(price) AS basket_revenue_brl
    FROM fact_order_items
    WHERE order_id IN (SELECT order_id FROM dim_orders WHERE order_status = 'delivered')
    GROUP BY order_id
)
SELECT 
    CASE 
        WHEN item_count = 1 THEN '1 Item'
        WHEN item_count = 2 THEN '2 Items'
        WHEN item_count BETWEEN 3 AND 5 THEN '3-5 Items'
        ELSE '6+ Items'
    END AS basket_size_tier,
    COUNT(order_id) AS order_count,
    ROUND(COUNT(order_id) * 100.0 / (SELECT COUNT(*) FROM order_basket), 2) AS order_pct,
    ROUND(SUM(basket_revenue_brl), 2) AS total_revenue_brl,
    ROUND(AVG(basket_revenue_brl), 2) AS aov_brl
FROM order_basket
GROUP BY basket_size_tier
ORDER BY order_count DESC;;

-- ==============================================================================
-- Query 13: Carrier SLA Breach & Late Delivery Severity
-- Tier: 3 | Question: What percentage of delivered orders breached their estimated delivery dates, and what is the distribution of delay duration?
-- Filter: Includes only completed orders (order_status = 'delivered') with non-null customer delivery timestamps.
-- ==============================================================================
WITH delivery_diffs AS (
    SELECT 
        order_id,
        DATEDIFF(order_delivered_customer_date, order_estimated_delivery_date) AS delay_days
    FROM dim_orders
    WHERE order_status = 'delivered' 
      AND order_delivered_customer_date IS NOT NULL
)
SELECT 
    CASE 
        WHEN delay_days <= 0 THEN 'On-Time / Ahead of Schedule'
        WHEN delay_days BETWEEN 1 AND 3 THEN 'Minor Delay (1-3 Days)'
        WHEN delay_days BETWEEN 4 AND 7 THEN 'Moderate Delay (4-7 Days)'
        ELSE 'Severe Delay (8+ Days)'
    END AS sla_performance_tier,
    COUNT(order_id) AS order_count,
    ROUND(COUNT(order_id) * 100.0 / (SELECT COUNT(*) FROM delivery_diffs), 2) AS percentage_of_orders,
    ROUND(AVG(CASE WHEN delay_days > 0 THEN delay_days ELSE 0 END), 1) AS avg_delay_days_when_late
FROM delivery_diffs
GROUP BY sla_performance_tier
ORDER BY order_count DESC;;

-- ==============================================================================
-- Query 14: Macro Sector Profitability & Margin Contribution Benchmark
-- Tier: 3 | Question: Under our documented category benchmark margins, which macro sectors deliver the highest gross profit (R$), and what is the platform's blended gross margin %?
-- Filter: Includes only completed orders (order_status = 'delivered'). Revenue excludes freight. Applies benchmark COGS/Margin rates from config.
-- ==============================================================================
WITH category_profits AS (
    SELECT 
        p.category_group,
        SUM(i.price) AS revenue_brl,
        SUM(i.price * p.assumed_cogs_rate) AS estimated_cogs_brl,
        SUM(i.price * p.assumed_gross_margin_rate) AS estimated_gross_profit_brl
    FROM fact_order_items i
    JOIN dim_orders o ON i.order_id = o.order_id
    JOIN dim_products p ON i.product_id = p.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY p.category_group
)
SELECT 
    category_group,
    ROUND(revenue_brl, 2) AS item_revenue_brl,
    ROUND(estimated_cogs_brl, 2) AS estimated_cogs_brl,
    ROUND(estimated_gross_profit_brl, 2) AS gross_profit_brl,
    ROUND(estimated_gross_profit_brl * 100.0 / revenue_brl, 2) AS gross_margin_pct
FROM category_profits
ORDER BY gross_profit_brl DESC;;

-- ==============================================================================
-- Query 15: Top 1% High-Value Customer Concentration
-- Tier: 3 | Question: What percentage of total platform item revenue is generated by the top 1% highest-spending customers?
-- Filter: Includes only completed orders (order_status = 'delivered'). Excludes freight. Groups by customer_unique_id.
-- ==============================================================================
WITH customer_spend AS (
    SELECT 
        c.customer_unique_id,
        SUM(i.price) AS total_spend_brl
    FROM dim_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
ranked_customers AS (
    SELECT 
        customer_unique_id,
        total_spend_brl,
        PERCENT_RANK() OVER (ORDER BY total_spend_brl DESC) AS percentile_rank
    FROM customer_spend
)
SELECT 
    CASE WHEN percentile_rank <= 0.01 THEN 'Top 1% Customers' ELSE 'Bottom 99% Customers' END AS customer_tier,
    COUNT(customer_unique_id) AS total_customers,
    ROUND(SUM(total_spend_brl), 2) AS cumulative_spend_brl,
    ROUND(SUM(total_spend_brl) * 100.0 / (SELECT SUM(total_spend_brl) FROM customer_spend), 2) AS spend_share_pct,
    ROUND(AVG(total_spend_brl), 2) AS avg_spend_per_customer_brl
FROM ranked_customers
GROUP BY customer_tier;;

-- ==============================================================================
-- Query 16: Seller Pareto Revenue Concentration (80/20 Rule)
-- Tier: 3 | Question: What proportion of active sellers account for 80% of total marketplace sales volume?
-- Filter: Includes only completed orders (order_status = 'delivered'). Excludes freight.
-- ==============================================================================
WITH seller_revenues AS (
    SELECT 
        s.seller_id,
        SUM(i.price) AS seller_revenue_brl
    FROM fact_order_items i
    JOIN dim_orders o ON i.order_id = o.order_id
    JOIN dim_sellers s ON i.seller_id = s.seller_id
    WHERE o.order_status = 'delivered'
    GROUP BY s.seller_id
),
seller_cumulative AS (
    SELECT 
        seller_id,
        seller_revenue_brl,
        SUM(seller_revenue_brl) OVER (ORDER BY seller_revenue_brl DESC) AS running_revenue_brl,
        SUM(seller_revenue_brl) OVER () AS total_marketplace_revenue_brl,
        ROW_NUMBER() OVER (ORDER BY seller_revenue_brl DESC) AS seller_rank,
        COUNT(*) OVER () AS total_active_sellers
    FROM seller_revenues
)
SELECT 
    CASE 
        WHEN running_revenue_brl <= (0.80 * total_marketplace_revenue_brl) THEN 'Top Sellers (Generating 80% GMV)'
        ELSE 'Long-Tail Sellers (Remaining 20% GMV)'
    END AS seller_segment,
    COUNT(seller_id) AS seller_count,
    ROUND(COUNT(seller_id) * 100.0 / MAX(total_active_sellers), 2) AS seller_pct,
    ROUND(SUM(seller_revenue_brl), 2) AS total_sales_brl,
    ROUND(SUM(seller_revenue_brl) * 100.0 / MAX(total_marketplace_revenue_brl), 2) AS actual_revenue_pct
FROM seller_cumulative
GROUP BY seller_segment;;

-- ==============================================================================
-- Query 17: Month-over-Month (MoM) Revenue & Growth Velocity
-- Tier: 4 | Question: What is the monthly delivered item revenue, previous month revenue using LAG(), and MoM percentage growth rate from 2017 to 2018?
-- Filter: Includes completed orders (order_status = 'delivered') between Jan 2017 and Aug 2018 (full operational period). Excludes freight.
-- ==============================================================================
WITH monthly_sales AS (
    SELECT 
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS order_month,
        ROUND(SUM(i.price), 2) AS current_month_revenue_brl,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM dim_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
)
SELECT 
    order_month,
    current_month_revenue_brl,
    LAG(current_month_revenue_brl, 1) OVER (ORDER BY order_month) AS previous_month_revenue_brl,
    ROUND((current_month_revenue_brl - LAG(current_month_revenue_brl, 1) OVER (ORDER BY order_month)) * 100.0 / 
          LAG(current_month_revenue_brl, 1) OVER (ORDER BY order_month), 2) AS mom_growth_pct,
    order_count
FROM monthly_sales
ORDER BY order_month;;

-- ==============================================================================
-- Query 18: Cumulative Running Sales Total Across Platform History
-- Tier: 4 | Question: How did total delivered merchandise revenue accumulate month-by-month toward multi-million BRL milestones?
-- Filter: Includes completed orders (order_status = 'delivered') between Jan 2017 and Aug 2018. Excludes freight.
-- ==============================================================================
WITH monthly_revenue AS (
    SELECT 
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS purchase_month,
        ROUND(SUM(i.price), 2) AS monthly_revenue_brl
    FROM dim_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
)
SELECT 
    purchase_month,
    monthly_revenue_brl,
    ROUND(SUM(monthly_revenue_brl) OVER (ORDER BY purchase_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_cumulative_revenue_brl
FROM monthly_revenue
ORDER BY purchase_month;;

-- ==============================================================================
-- Query 19: Top 3 Best-Selling Product Categories in Each Macro Sector
-- Tier: 4 | Question: What are the top 3 best-selling product categories within each macro sector using DENSE_RANK()?
-- Filter: Includes completed orders (order_status = 'delivered'). Excludes freight.
-- ==============================================================================
WITH category_sales AS (
    SELECT 
        p.category_group,
        p.product_category_name_english AS category,
        ROUND(SUM(i.price), 2) AS total_sales_brl,
        COUNT(i.order_item_id) AS units_sold
    FROM fact_order_items i
    JOIN dim_orders o ON i.order_id = o.order_id
    JOIN dim_products p ON i.product_id = p.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY p.category_group, p.product_category_name_english
),
ranked_categories AS (
    SELECT 
        category_group,
        category,
        total_sales_brl,
        units_sold,
        DENSE_RANK() OVER (PARTITION BY category_group ORDER BY total_sales_brl DESC) AS category_rank
    FROM category_sales
)
SELECT 
    category_group,
    category_rank,
    category,
    total_sales_brl,
    units_sold
FROM ranked_categories
WHERE category_rank <= 3
ORDER BY category_group, category_rank;;

-- ==============================================================================
-- Query 20: Customer Purchase Latency (Days Between Successive Orders)
-- Tier: 4 | Question: For repeat customers who placed multiple orders, what is the average and range of days elapsed between consecutive orders?
-- Filter: Includes completed orders (order_status = 'delivered'). Partitioned by customer_unique_id.
-- ==============================================================================
WITH customer_order_timeline AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        LAG(o.order_purchase_timestamp, 1) OVER (
            PARTITION BY c.customer_unique_id 
            ORDER BY o.order_purchase_timestamp
        ) AS previous_purchase_timestamp
    FROM dim_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),
order_intervals AS (
    SELECT 
        customer_unique_id,
        DATEDIFF(order_purchase_timestamp, previous_purchase_timestamp) AS days_since_last_order
    FROM customer_order_timeline
    WHERE previous_purchase_timestamp IS NOT NULL
)
SELECT 
    COUNT(days_since_last_order) AS repeat_reorder_events,
    ROUND(AVG(days_since_last_order), 1) AS avg_days_between_orders,
    MIN(days_since_last_order) AS min_days_between_orders,
    MAX(days_since_last_order) AS max_days_between_orders
FROM order_intervals;;

-- ==============================================================================
-- Query 21: Customer Spend Deciles & Revenue Concentration (NTILE 10)
-- Tier: 4 | Question: Dividing all unique customers into 10 equal deciles by total spend, how much revenue is concentrated in each tier?
-- Filter: Includes completed orders (order_status = 'delivered'). Excludes freight.
-- ==============================================================================
WITH customer_spend AS (
    SELECT 
        c.customer_unique_id,
        SUM(i.price) AS total_spend_brl
    FROM dim_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_deciles AS (
    SELECT 
        customer_unique_id,
        total_spend_brl,
        NTILE(10) OVER (ORDER BY total_spend_brl DESC) AS spend_decile
    FROM customer_spend
)
SELECT 
    spend_decile,
    COUNT(customer_unique_id) AS customer_count,
    ROUND(MIN(total_spend_brl), 2) AS min_spend_brl,
    ROUND(MAX(total_spend_brl), 2) AS max_spend_brl,
    ROUND(SUM(total_spend_brl), 2) AS decile_revenue_brl,
    ROUND(SUM(total_spend_brl) * 100.0 / (SELECT SUM(total_spend_brl) FROM customer_spend), 2) AS revenue_share_pct
FROM customer_deciles
GROUP BY spend_decile
ORDER BY spend_decile ASC;;

-- ==============================================================================
-- Query 22: 3-Month Moving Average of Monthly Revenue
-- Tier: 4 | Question: What is the 3-month trailing moving average of delivered sales revenue, and how does it smooth seasonality?
-- Filter: Includes completed orders (order_status = 'delivered') between Jan 2017 and Aug 2018. Excludes freight.
-- ==============================================================================
WITH monthly_revenue AS (
    SELECT 
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS purchase_month,
        ROUND(SUM(i.price), 2) AS monthly_revenue_brl
    FROM dim_orders o
    JOIN fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
)
SELECT 
    purchase_month,
    monthly_revenue_brl,
    ROUND(AVG(monthly_revenue_brl) OVER (
        ORDER BY purchase_month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3m_revenue_brl
FROM monthly_revenue
ORDER BY purchase_month;;


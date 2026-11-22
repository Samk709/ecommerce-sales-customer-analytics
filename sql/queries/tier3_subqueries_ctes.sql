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


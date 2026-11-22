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


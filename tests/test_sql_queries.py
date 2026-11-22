"""
SQL Query Result Verification Test Suite
Verifies mathematical consistency, reconciliation across queries, and data integrity.
"""

import pytest
from sqlalchemy import text
from src.database.db_connection import get_engine, test_connection as check_mysql_connection

def test_connection():
    """Verify that Python connects to MySQL and returns True using assert."""
    assert check_mysql_connection() is True

@pytest.fixture(scope="session")
def db_conn():
    if not check_mysql_connection():
        pytest.skip("MySQL database not reachable. Skipping SQL query tests.")
    engine = get_engine(include_database=True)
    with engine.connect() as conn:
        yield conn

def test_revenue_cross_calculation_reconciliation(db_conn):
    """
    Verify that total delivered item revenue calculated via JOIN matches
    the total calculated via a subquery IN filter.
    """
    # Method A: Direct JOIN
    sql_a = text("""
        SELECT ROUND(SUM(i.price), 2) AS total_revenue
        FROM dim_orders o
        JOIN fact_order_items i ON o.order_id = i.order_id
        WHERE o.order_status = 'delivered';
    """)
    rev_a = db_conn.execute(sql_a).scalar()

    # Method B: Subquery
    sql_b = text("""
        SELECT ROUND(SUM(price), 2) AS total_revenue
        FROM fact_order_items
        WHERE order_id IN (
            SELECT order_id FROM dim_orders WHERE order_status = 'delivered'
        );
    """)
    rev_b = db_conn.execute(sql_b).scalar()

    assert rev_a is not None and rev_b is not None
    assert rev_a == rev_b, f"Revenue mismatch: Method A={rev_a} vs Method B={rev_b}"
    # Verify exact empirical figure: R$ 13,221,498.11
    assert float(rev_a) == 13221498.11

def test_order_status_aggregation_integrity(db_conn):
    """
    Verify that the sum of order counts across all statuses in Query 3
    equals exactly the total rows in dim_orders (99,441).
    """
    sql = text("""
        SELECT SUM(order_count) AS total_orders
        FROM (
            SELECT order_status, COUNT(order_id) AS order_count
            FROM dim_orders
            GROUP BY order_status
        ) AS status_counts;
    """)
    total_orders = db_conn.execute(sql).scalar()
    assert total_orders == 99441

def test_repeat_vs_onetime_customer_revenue_balance(db_conn):
    """
    Verify that repeat revenue + one-time customer revenue equals total delivered revenue.
    """
    sql = text("""
        WITH customer_orders AS (
            SELECT 
                c.customer_unique_id,
                COUNT(DISTINCT o.order_id) AS order_count,
                SUM(i.price) AS total_spend
            FROM dim_orders o
            JOIN dim_customers c ON o.customer_id = c.customer_id
            JOIN fact_order_items i ON o.order_id = i.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        )
        SELECT 
            ROUND(SUM(CASE WHEN order_count = 1 THEN total_spend ELSE 0 END), 2) AS onetime_rev,
            ROUND(SUM(CASE WHEN order_count > 1 THEN total_spend ELSE 0 END), 2) AS repeat_rev,
            ROUND(SUM(total_spend), 2) AS total_combined_rev
        FROM customer_orders;
    """)
    row = db_conn.execute(sql).fetchone()
    onetime_rev = float(row[0])
    repeat_rev = float(row[1])
    combined_rev = float(row[2])

    assert round(onetime_rev + repeat_rev, 2) == combined_rev
    assert combined_rev == 13221498.11

def test_running_cumulative_sales_integrity(db_conn):
    """
    Verify that the cumulative running total at the final month (2018-08)
    equals the sum of monthly revenues for that exact window.
    """
    sql_monthly_sum = text("""
        SELECT ROUND(SUM(i.price), 2)
        FROM dim_orders o
        JOIN fact_order_items i ON o.order_id = i.order_id
        WHERE o.order_status = 'delivered'
          AND o.order_purchase_timestamp >= '2017-01-01'
          AND o.order_purchase_timestamp < '2018-09-01';
    """)
    expected_sum = float(db_conn.execute(sql_monthly_sum).scalar())

    sql_window = text("""
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
        SELECT running_cumulative_revenue_brl
        FROM (
            SELECT 
                purchase_month,
                ROUND(SUM(monthly_revenue_brl) OVER (ORDER BY purchase_month), 2) AS running_cumulative_revenue_brl
            FROM monthly_revenue
        ) AS t
        ORDER BY purchase_month DESC
        LIMIT 1;
    """)
    final_cumulative = float(db_conn.execute(sql_window).scalar())

    assert abs(final_cumulative - expected_sum) <= 0.05

def test_decile_revenue_and_share_reconciliation(db_conn):
    """
    Verify that across all 10 customer spend deciles (Query 21):
    1. Sum of decile revenues equals total delivered item revenue (R$ 13,221,498.11).
    2. Sum of revenue share percentages equals 100.00%.
    """
    sql = text("""
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
        ),
        decile_summary AS (
            SELECT 
                spend_decile,
                ROUND(SUM(total_spend_brl), 2) AS decile_revenue_brl,
                ROUND(SUM(total_spend_brl) * 100.0 / (SELECT SUM(total_spend_brl) FROM customer_spend), 2) AS revenue_share_pct
            FROM customer_deciles
            GROUP BY spend_decile
        )
        SELECT 
            ROUND(SUM(decile_revenue_brl), 2) AS sum_decile_revenue,
            ROUND(SUM(revenue_share_pct), 2) AS sum_share_pct
        FROM decile_summary;
    """)
    row = db_conn.execute(sql).fetchone()
    sum_revenue = float(row[0])
    sum_share = float(row[1])

    assert abs(sum_revenue - 13221498.11) <= 0.05
    assert abs(sum_share - 100.00) <= 0.05

def test_group_revenue_and_freight_reconciliation(db_conn):
    """
    Verify that summing across all 11 category groups (Query 9)
    equals the platform totals from Query 1:
    - Total items sold = 110,197
    - Total item revenue = R$ 13,221,498.11
    - Total freight = R$ 2,198,275.64
    """
    sql = text("""
        WITH group_aggregates AS (
            SELECT 
                p.category_group,
                COUNT(i.order_item_id) AS items_sold,
                ROUND(SUM(i.price), 2) AS total_item_revenue_brl,
                ROUND(SUM(i.freight_value), 2) AS total_freight_brl
            FROM fact_order_items i
            JOIN dim_orders o ON i.order_id = o.order_id
            JOIN dim_products p ON i.product_id = p.product_id
            WHERE o.order_status = 'delivered'
            GROUP BY p.category_group
        )
        SELECT 
            SUM(items_sold) AS sum_items,
            ROUND(SUM(total_item_revenue_brl), 2) AS sum_revenue,
            ROUND(SUM(total_freight_brl), 2) AS sum_freight
        FROM group_aggregates;
    """)
    row = db_conn.execute(sql).fetchone()
    sum_items = int(row[0])
    sum_revenue = float(row[1])
    sum_freight = float(row[2])

    assert sum_items == 110197
    assert sum_revenue == 13221498.11
    assert sum_freight == 2198275.64

def test_sla_tier_order_counts_reconciliation(db_conn):
    """
    Verify that summing order counts across all 4 SLA delivery tiers (Query 13)
    equals exactly the filtered delivered orders count with non-null delivery dates (96,470).
    """
    sql = text("""
        WITH delivery_diffs AS (
            SELECT 
                order_id,
                DATEDIFF(order_delivered_customer_date, order_estimated_delivery_date) AS delay_days
            FROM dim_orders
            WHERE order_status = 'delivered' 
              AND order_delivered_customer_date IS NOT NULL
        ),
        tier_counts AS (
            SELECT 
                CASE 
                    WHEN delay_days <= 0 THEN 'On-Time / Ahead of Schedule'
                    WHEN delay_days BETWEEN 1 AND 3 THEN 'Minor Delay (1-3 Days)'
                    WHEN delay_days BETWEEN 4 AND 7 THEN 'Moderate Delay (4-7 Days)'
                    ELSE 'Severe Delay (8+ Days)'
                END AS sla_performance_tier,
                COUNT(order_id) AS order_count
            FROM delivery_diffs
            GROUP BY sla_performance_tier
        )
        SELECT SUM(order_count) FROM tier_counts;
    """)
    total_tier_orders = int(db_conn.execute(sql).scalar())

    sql_expected = text("""
        SELECT COUNT(order_id) 
        FROM dim_orders 
        WHERE order_status = 'delivered' 
          AND order_delivered_customer_date IS NOT NULL;
    """)
    expected_orders = int(db_conn.execute(sql_expected).scalar())

    assert expected_orders == 96470
    assert total_tier_orders == 96470

def test_q14_profitability_group_sums_and_totals(db_conn):
    """
    Verify that summing across all 11 category groups in Query 14:
    1. Sum of estimated COGS equals R$ 7,832,679.15
    2. Sum of gross profit equals R$ 5,388,818.98
    3. Sum of group COGS + GP equals platform item revenue (R$ 13,221,498.11) within 0.05
    4. Overall blended margin is 40.76% (within 0.05%)
    """
    sql = text("""
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
            ROUND(SUM(ROUND(estimated_cogs_brl, 2)), 2) AS sum_cogs,
            ROUND(SUM(ROUND(estimated_gross_profit_brl, 2)), 2) AS sum_gross_profit,
            ROUND(SUM(ROUND(revenue_brl, 2)), 2) AS sum_revenue
        FROM category_profits;
    """)
    row = db_conn.execute(sql).fetchone()
    sum_cogs = float(row[0])
    sum_gp = float(row[1])
    sum_rev = float(row[2])

    assert sum_cogs == 7832679.15
    assert sum_gp == 5388818.98
    assert abs((sum_cogs + sum_gp) - sum_rev) <= 0.05
    assert sum_rev == 13221498.11
    blended_margin = round(sum_gp * 100.0 / sum_rev, 2)
    assert blended_margin == 40.76

def test_q5_csat_review_counts_and_shares_sum(db_conn):
    """
    Verify that in Query 5 (CSAT Rating Distribution):
    1. Total reviews across all star ratings sum to exactly 96,361.
    2. Review share percentages sum to 100.00% (within 0.05%).
    """
    sql = text("""
        WITH review_dist AS (
            SELECT 
                r.review_score,
                COUNT(r.review_surrogate_id) AS total_reviews,
                ROUND(COUNT(r.review_surrogate_id) * 100.0 / SUM(COUNT(r.review_surrogate_id)) OVER(), 2) AS percentage_of_reviews
            FROM fact_order_reviews r
            JOIN dim_orders o ON r.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY r.review_score
        )
        SELECT 
            SUM(total_reviews) AS sum_reviews,
            ROUND(SUM(percentage_of_reviews), 2) AS sum_shares
        FROM review_dist;
    """)
    row = db_conn.execute(sql).fetchone()
    sum_reviews = int(row[0])
    sum_shares = float(row[1])

    assert sum_reviews == 96361
    assert abs(sum_shares - 100.00) <= 0.05

def test_q8_standardized_date_late_definition(db_conn):
    """
    Verify Query 8 with standardized date comparison DATE(delivered) <= DATE(estimated):
    1. On-Time / Early review count is 89,944
    2. Delayed / Late review count is 6,409
    3. Total reviews evaluated equals 96,353
    """
    sql = text("""
        SELECT 
            CASE 
                WHEN DATE(o.order_delivered_customer_date) <= DATE(o.order_estimated_delivery_date) THEN 'On-Time / Early'
                ELSE 'Delayed / Late'
            END AS delivery_performance,
            COUNT(r.review_surrogate_id) AS review_count
        FROM dim_orders o
        JOIN fact_order_reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered' 
          AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY delivery_performance;
    """)
    rows = dict(db_conn.execute(sql).fetchall())
    ontime_count = rows["On-Time / Early"]
    delayed_count = rows["Delayed / Late"]

    assert ontime_count == 89944
    assert delayed_count == 6409
    assert ontime_count + delayed_count == 96353



-- ════════════════════════════════════════════════════════
-- REVENUE TRENDS — Month over Month
-- Business Question: How is revenue trending over time?
-- What is our MoM growth rate?
-- ════════════════════════════════════════════════════════

WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', o.order_purchase_timestamp::timestamp) AS month,
        COUNT(DISTINCT o.order_id)          AS total_orders,
        COUNT(DISTINCT o.customer_id)       AS unique_customers,
        ROUND(SUM(p.total_payment)::numeric, 2) AS revenue
    FROM fact_orders o
    JOIN fact_payments p ON o.order_id = p.order_id
    GROUP BY DATE_TRUNC('month', o.order_purchase_timestamp::timestamp)
)

SELECT
    TO_CHAR(month, 'YYYY-MM')          AS month,
    total_orders,
    unique_customers,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0 /
        NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1
    )                                  AS mom_growth_pct
FROM monthly_revenue
ORDER BY month;
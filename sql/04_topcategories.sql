-- ════════════════════════════════════════════════════════
-- TOP PERFORMING CATEGORIES
-- Business Question: Which product categories drive 
-- the most revenue, orders and average order value?
-- ════════════════════════════════════════════════════════

WITH category_revenue AS (
    SELECT
        COALESCE(p.product_category_name_english, 'unknown') AS category,
        COUNT(DISTINCT o.order_id)                AS total_orders,
        ROUND(SUM(pay.total_payment)::numeric, 2) AS total_revenue,
        ROUND(AVG(pay.total_payment)::numeric, 2) AS avg_order_value,
        ROUND(AVG(r.review_score)::numeric, 2)    AS avg_review_score
    FROM fact_items i
    JOIN dim_products p   ON i.product_id = p.product_id
    JOIN fact_orders o    ON i.order_id = o.order_id
    JOIN fact_payments pay ON o.order_id = pay.order_id
    LEFT JOIN fact_reviews r ON o.order_id = r.order_id
    GROUP BY p.product_category_name_english
)

SELECT
    category,
    total_orders,
    total_revenue,
    avg_order_value,
    avg_review_score,
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM category_revenue
ORDER BY total_revenue DESC
LIMIT 15;
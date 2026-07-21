-- ════════════════════════════════════════════════════════
-- SEMANTIC LAYER — Centralized KPI Views
-- All outputs (Streamlit, AI, PDF) query these views
-- Never raw tables — this is the single source of truth
-- ════════════════════════════════════════════════════════

-- View 1: Monthly Revenue KPI
CREATE OR REPLACE VIEW v_monthly_revenue AS
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp::timestamp) AS month,
    COUNT(DISTINCT o.order_id)              AS total_orders,
    COUNT(DISTINCT o.customer_id)           AS unique_customers,
    ROUND(SUM(p.total_payment)::numeric, 2) AS revenue,
    ROUND(AVG(p.total_payment)::numeric, 2) AS avg_order_value
FROM fact_orders o
JOIN fact_payments p ON o.order_id = p.order_id
GROUP BY DATE_TRUNC('month', o.order_purchase_timestamp::timestamp);

-- View 2: Customer Churn Risk
CREATE OR REPLACE VIEW v_churn_risk AS
SELECT
    c.customer_unique_id,
    COUNT(DISTINCT o.order_id)                        AS total_orders,
    ROUND(SUM(p.total_payment)::numeric, 2)           AS total_spent,
    MAX(o.order_purchase_timestamp::timestamp)::date  AS last_order_date,
    CURRENT_DATE - MAX(o.order_purchase_timestamp::timestamp)::date AS days_since_last_order,
    CASE
        WHEN CURRENT_DATE - MAX(o.order_purchase_timestamp::timestamp)::date > 180 THEN 'High Risk'
        WHEN CURRENT_DATE - MAX(o.order_purchase_timestamp::timestamp)::date > 90  THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS churn_risk_label
FROM dim_customers c
JOIN fact_orders o   ON c.customer_id = o.customer_id
JOIN fact_payments p ON o.order_id = p.order_id
GROUP BY c.customer_unique_id;

-- View 3: RFM Segments (single source of truth)
CREATE OR REPLACE VIEW v_rfm_segments AS
WITH rfm AS (
    SELECT
        c.customer_unique_id,
        CURRENT_DATE - MAX(o.order_purchase_timestamp::timestamp)::date AS recency_days,
        COUNT(DISTINCT o.order_id)              AS frequency,
        ROUND(SUM(p.total_payment)::numeric, 2) AS monetary
    FROM dim_customers c
    JOIN fact_orders o   ON c.customer_id = o.customer_id
    JOIN fact_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
),
scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm
)
SELECT *,
    CASE
        WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'Potential Loyalists'
        WHEN r_score >= 4 AND (f_score + m_score) <= 4 THEN 'New Customers'
        WHEN r_score <= 2 AND (f_score + m_score) >= 8 THEN 'At Risk'
        ELSE 'Need Attention'
    END AS segment
FROM scored;

-- View 4: Category Performance
CREATE OR REPLACE VIEW v_category_performance AS
SELECT
    COALESCE(p.product_category_name_english, 'unknown') AS category,
    COUNT(DISTINCT o.order_id)                AS total_orders,
    ROUND(SUM(pay.total_payment)::numeric, 2) AS total_revenue,
    ROUND(AVG(pay.total_payment)::numeric, 2) AS avg_order_value,
    ROUND(AVG(r.review_score)::numeric, 2)    AS avg_review_score
FROM fact_items i
JOIN dim_products p    ON i.product_id = p.product_id
JOIN fact_orders o     ON i.order_id = o.order_id
JOIN fact_payments pay ON o.order_id = pay.order_id
LEFT JOIN fact_reviews r ON o.order_id = r.order_id
GROUP BY p.product_category_name_english;

-- View 5: Seller Risk Rating
CREATE OR REPLACE VIEW v_seller_risk AS
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT o.order_id)                    AS total_orders,
    ROUND(AVG(o.delivery_delay_days)::numeric, 1) AS avg_delay_days,
    ROUND(AVG(r.review_score)::numeric, 2)        AS avg_review_score,
    ROUND(
        SUM(CASE WHEN o.delivery_delay_days > 0 THEN 1 ELSE 0 END) * 100.0 /
        COUNT(DISTINCT o.order_id), 1
    ) AS late_pct,
    CASE
        WHEN ROUND(SUM(CASE WHEN o.delivery_delay_days > 0 THEN 1 ELSE 0 END) * 100.0 /
             COUNT(DISTINCT o.order_id), 1) >= 50 THEN 'High Risk'
        WHEN ROUND(SUM(CASE WHEN o.delivery_delay_days > 0 THEN 1 ELSE 0 END) * 100.0 /
             COUNT(DISTINCT o.order_id), 1) >= 25 THEN 'Medium Risk'
        ELSE 'Good'
    END AS risk_rating
FROM dim_sellers s
JOIN fact_items i  ON s.seller_id = i.seller_id
JOIN fact_orders o ON i.order_id = o.order_id
LEFT JOIN fact_reviews r ON o.order_id = r.order_id
GROUP BY s.seller_id, s.seller_city, s.seller_state
HAVING COUNT(DISTINCT o.order_id) >= 50;
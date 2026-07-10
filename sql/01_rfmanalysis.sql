-- ════════════════════════════════════════════════════════
-- RFM ANALYSIS
-- Business Question: Who are our most valuable customers?
-- RFM = Recency (how recently they bought)
--       Frequency (how many times they bought)
--       Monetary (how much they spent)
-- ════════════════════════════════════════════════════════

WITH rfm_base AS (
    SELECT
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,

        -- Recency: days since last purchase
        CURRENT_DATE - MAX(o.order_purchase_timestamp)::date AS recency_days,

        -- Frequency: number of orders
        COUNT(DISTINCT o.order_id) AS frequency,

        -- Monetary: total amount spent
        ROUND(SUM(p.total_payment)::numeric, 2) AS monetary

    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    JOIN fact_payments p ON o.order_id = p.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY c.customer_unique_id, c.customer_city, c.customer_state
),

rfm_scored AS (
    SELECT *,
        -- Score 1-5 (5 = best)
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)      AS m_score
    FROM rfm_base
),

rfm_segments AS (
    SELECT *,
        ROUND((r_score + f_score + m_score) / 3.0, 2) AS rfm_avg,
        CASE
            WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
            WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
            WHEN (r_score + f_score + m_score) >= 7  THEN 'Potential Loyalists'
            WHEN r_score >= 4 AND (f_score + m_score) <= 4 THEN 'New Customers'
            WHEN r_score <= 2 AND (f_score + m_score) >= 8 THEN 'At Risk'
            ELSE 'Need Attention'
        END AS segment
    FROM rfm_scored
)

SELECT
    segment,
    COUNT(*)                        AS customer_count,
    ROUND(AVG(recency_days), 0)     AS avg_recency_days,
    ROUND(AVG(frequency), 2)        AS avg_frequency,
    ROUND(AVG(monetary), 2)         AS avg_monetary,
    ROUND(SUM(monetary), 2)         AS total_revenue
FROM rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC;
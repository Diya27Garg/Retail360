-- ════════════════════════════════════════════════════════
-- DELIVERY PERFORMANCE BY SELLER
-- Business Question: Which sellers are consistently 
-- late? How does delivery delay affect review scores?
-- ════════════════════════════════════════════════════════

WITH seller_delivery AS (
    SELECT
        s.seller_id,
        s.seller_city,
        s.seller_state,
        COUNT(DISTINCT o.order_id)                    AS total_orders,
        ROUND(AVG(o.delivery_delay_days)::numeric, 1) AS avg_delay_days,
        ROUND(AVG(r.review_score)::numeric, 2)        AS avg_review_score,
        SUM(CASE WHEN o.delivery_delay_days > 0 
            THEN 1 ELSE 0 END)                        AS late_deliveries,
        ROUND(
            SUM(CASE WHEN o.delivery_delay_days > 0 
                THEN 1 ELSE 0 END) * 100.0 /
            COUNT(DISTINCT o.order_id), 1
        )                                             AS late_pct
    FROM dim_sellers s
    JOIN fact_items i  ON s.seller_id = i.seller_id
    JOIN fact_orders o ON i.order_id = o.order_id
    LEFT JOIN fact_reviews r ON o.order_id = r.order_id
    GROUP BY s.seller_id, s.seller_city, s.seller_state
    HAVING COUNT(DISTINCT o.order_id) >= 50
)

SELECT
    seller_id,
    seller_city,
    seller_state,
    total_orders,
    avg_delay_days,
    late_deliveries,
    late_pct,
    avg_review_score,
    CASE
        WHEN late_pct >= 50 THEN 'High Risk'
        WHEN late_pct >= 25 THEN 'Medium Risk'
        ELSE 'Good'
    END AS seller_risk_rating
FROM seller_delivery
ORDER BY late_pct DESC
LIMIT 20;
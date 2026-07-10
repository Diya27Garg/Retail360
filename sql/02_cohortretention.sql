-- ════════════════════════════════════════════════════════
-- COHORT RETENTION ANALYSIS
-- Business Question: Of customers who first bought in 
-- month X, how many came back in subsequent months?
-- ════════════════════════════════════════════════════════

WITH first_purchase AS (
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', MIN(o.order_purchase_timestamp::timestamp)) AS cohort_month
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
),

order_months AS (
    SELECT
        c.customer_unique_id,
        DATE_TRUNC('month', o.order_purchase_timestamp::timestamp) AS order_month
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
),

cohort_data AS (
    SELECT
        fp.cohort_month,
        om.order_month,
        EXTRACT(YEAR FROM AGE(om.order_month, fp.cohort_month)) * 12 +
        EXTRACT(MONTH FROM AGE(om.order_month, fp.cohort_month)) AS month_number,
        COUNT(DISTINCT fp.customer_unique_id) AS customers
    FROM first_purchase fp
    JOIN order_months om ON fp.customer_unique_id = om.customer_unique_id
    GROUP BY fp.cohort_month, om.order_month, month_number
),

cohort_sizes AS (
    SELECT cohort_month, customers AS cohort_size
    FROM cohort_data
    WHERE month_number = 0
)

SELECT
    TO_CHAR(cd.cohort_month, 'YYYY-MM')     AS cohort,
    cd.month_number,
    cd.customers,
    cs.cohort_size,
    ROUND(cd.customers * 100.0 / cs.cohort_size, 1) AS retention_rate
FROM cohort_data cd
JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
WHERE cd.cohort_month >= '2017-01-01'
  AND cd.month_number <= 6
ORDER BY cd.cohort_month, cd.month_number;
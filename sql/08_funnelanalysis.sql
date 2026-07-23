-- ════════════════════════════════════════════════════════
-- ORDER FUNNEL ANALYSIS
-- Business Question: Where are we losing orders in the
-- fulfillment journey? What is the conversion rate at
-- each stage from placement to delivery?
-- This directly answers: "Why did fulfillment drop?"
-- ════════════════════════════════════════════════════════

WITH funnel_stages AS (
    SELECT
        COUNT(*)                                    AS total_orders,

        -- Stage 1: Order placed (all orders)
        COUNT(*) AS placed,

        -- Stage 2: Order approved
        COUNT(CASE WHEN order_approved_at 
            IS NOT NULL THEN 1 END)                 AS approved,

        -- Stage 3: Dispatched to carrier
        COUNT(CASE WHEN order_delivered_carrier_date 
            IS NOT NULL THEN 1 END)                 AS dispatched,

        -- Stage 4: Delivered to customer
        COUNT(CASE WHEN order_delivered_customer_date 
            IS NOT NULL THEN 1 END)                 AS delivered,

        -- Average time between each stage (hours)
        ROUND(AVG(
            EXTRACT(EPOCH FROM (
                order_approved_at::timestamp - 
                order_purchase_timestamp::timestamp
            )) / 3600
        )::numeric, 1)                              AS avg_hours_to_approval,

        ROUND(AVG(
            EXTRACT(EPOCH FROM (
                order_delivered_carrier_date::timestamp - 
                order_approved_at::timestamp
            )) / 3600
        )::numeric, 1)                              AS avg_hours_to_dispatch,

        ROUND(AVG(
            EXTRACT(EPOCH FROM (
                order_delivered_customer_date::timestamp - 
                order_delivered_carrier_date::timestamp
            )) / 3600
        )::numeric, 1)                              AS avg_hours_to_delivery

    FROM fact_orders
)

SELECT
    placed                                          AS stage_1_placed,
    approved                                        AS stage_2_approved,
    dispatched                                      AS stage_3_dispatched,
    delivered                                       AS stage_4_delivered,

    -- Drop-off at each stage
    placed - approved                               AS drop_placed_to_approved,
    approved - dispatched                           AS drop_approved_to_dispatched,
    dispatched - delivered                          AS drop_dispatched_to_delivered,

    -- Conversion rates
    ROUND(approved * 100.0 / placed, 1)             AS pct_approved,
    ROUND(dispatched * 100.0 / placed, 1)           AS pct_dispatched,
    ROUND(delivered * 100.0 / placed, 1)            AS pct_delivered,

    -- Time between stages
    avg_hours_to_approval,
    avg_hours_to_dispatch,
    avg_hours_to_delivery,

    -- Total end-to-end hours
    ROUND(
        avg_hours_to_approval + 
        avg_hours_to_dispatch + 
        avg_hours_to_delivery
    , 1)                                            AS avg_total_fulfillment_hours

FROM funnel_stages;
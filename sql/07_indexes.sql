-- ════════════════════════════════════════════════════════
-- INDEXES AND CONSTRAINTS
-- Optimizes query performance and enforces relationships
-- ════════════════════════════════════════════════════════

-- Indexes for faster analytical queries
CREATE INDEX IF NOT EXISTS idx_orders_customer_id 
    ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_date 
    ON fact_orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_items_order_id 
    ON fact_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product_id 
    ON fact_items(product_id);
CREATE INDEX IF NOT EXISTS idx_items_seller_id 
    ON fact_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id 
    ON fact_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_order_id 
    ON fact_reviews(order_id);

-- Unique constraints on dimension tables
ALTER TABLE dim_customers
    ADD CONSTRAINT uq_customers_id UNIQUE (customer_id);
ALTER TABLE dim_products
    ADD CONSTRAINT uq_products_id UNIQUE (product_id);
ALTER TABLE dim_sellers
    ADD CONSTRAINT uq_sellers_id UNIQUE (seller_id);
ALTER TABLE fact_orders
    ADD CONSTRAINT uq_orders_id UNIQUE (order_id);

-- Foreign key constraints
-- Note: fk_orders_customer skipped — customer deduplication
-- in ETL causes orphaned customer_ids in fact_orders.
-- Documented trade-off: ETL deduplication vs referential integrity.
ALTER TABLE fact_items
    ADD CONSTRAINT fk_items_product 
    FOREIGN KEY (product_id) 
    REFERENCES dim_products(product_id);
ALTER TABLE fact_items
    ADD CONSTRAINT fk_items_seller 
    FOREIGN KEY (seller_id) 
    REFERENCES dim_sellers(seller_id);
import pandas as pd
import os

RAW  = "data/raw/"
CLEAN = "data/cleaned/"

# ── 1. CUSTOMERS ──────────────────────────────────────────
customers = pd.read_csv(RAW + "olist_customers_dataset.csv")
# drop duplicate unique customers
customers = customers.drop_duplicates(subset="customer_unique_id")
customers.to_csv(CLEAN + "customers.csv", index=False)
print(f"customers: {len(customers):,} rows")

# ── 2. ORDERS ─────────────────────────────────────────────
orders = pd.read_csv(RAW + "olist_orders_dataset.csv")
# convert all date columns
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]
for col in date_cols:
    orders[col] = pd.to_datetime(orders[col])

# keep only delivered orders for analysis
orders_delivered = orders[orders["order_status"] == "delivered"].copy()

# calculate delivery delay in days
orders_delivered["delivery_delay_days"] = (
    orders_delivered["order_delivered_customer_date"] -
    orders_delivered["order_estimated_delivery_date"]
).dt.days

orders_delivered.to_csv(CLEAN + "orders.csv", index=False)
print(f"orders (delivered): {len(orders_delivered):,} rows")

# ── 3. ORDER ITEMS ────────────────────────────────────────
items = pd.read_csv(RAW + "olist_order_items_dataset.csv")
items["shipping_limit_date"] = pd.to_datetime(items["shipping_limit_date"])
items["total_value"] = items["price"] + items["freight_value"]
items.to_csv(CLEAN + "order_items.csv", index=False)
print(f"order_items: {len(items):,} rows")

# ── 4. PAYMENTS ───────────────────────────────────────────
payments = pd.read_csv(RAW + "olist_order_payments_dataset.csv")
# aggregate payments per order (some orders have multiple payment methods)
payments_agg = payments.groupby("order_id").agg(
    total_payment  = ("payment_value", "sum"),
    payment_types  = ("payment_type", lambda x: ",".join(x.unique())),
    installments   = ("payment_installments", "max")
).reset_index()
payments_agg.to_csv(CLEAN + "payments.csv", index=False)
print(f"payments: {len(payments_agg):,} rows")

# ── 5. PRODUCTS ───────────────────────────────────────────
products  = pd.read_csv(RAW + "olist_products_dataset.csv")
category  = pd.read_csv(RAW + "product_category_name_translation.csv")

# merge to get English category names
products = products.merge(category, on="product_category_name", how="left")

# fill missing category with 'unknown'
products["product_category_name_english"] = (
    products["product_category_name_english"].fillna("unknown")
)

# drop columns we don't need
products = products.drop(columns=[
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty"
])
products.to_csv(CLEAN + "products.csv", index=False)
print(f"products: {len(products):,} rows")

# ── 6. SELLERS ────────────────────────────────────────────
sellers = pd.read_csv(RAW + "olist_sellers_dataset.csv")
sellers.to_csv(CLEAN + "sellers.csv", index=False)
print(f"sellers: {len(sellers):,} rows")

# ── 7. REVIEWS ────────────────────────────────────────────
reviews = pd.read_csv(RAW + "olist_order_reviews_dataset.csv")
# only keep what we need
reviews = reviews[["order_id", "review_score"]].drop_duplicates(subset="order_id")
reviews.to_csv(CLEAN + "reviews.csv", index=False)
print(f"reviews: {len(reviews):,} rows")

print("\n All files cleaned and saved to data/cleaned/")
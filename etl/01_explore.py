import pandas as pd
import os

RAW_PATH = "data/raw/"

files = {
    "customers"   : "olist_customers_dataset.csv",
    "orders"      : "olist_orders_dataset.csv",
    "order_items" : "olist_order_items_dataset.csv",
    "payments"    : "olist_order_payments_dataset.csv",
    "reviews"     : "olist_order_reviews_dataset.csv",
    "products"    : "olist_products_dataset.csv",
    "sellers"     : "olist_sellers_dataset.csv",
    "geolocation" : "olist_geolocation_dataset.csv",
    "category"    : "product_category_name_translation.csv",
}

for name, filename in files.items():
    path = os.path.join(RAW_PATH, filename)
    df = pd.read_csv(path)
    print(f"\n{'='*50}")
    print(f"TABLE: {name.upper()}")
    print(f"Rows: {df.shape[0]:,} | Columns: {df.shape[1]}")
    print(f"Columns: {list(df.columns)}")
    print(f"Nulls:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
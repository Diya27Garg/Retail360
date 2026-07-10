import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

# ── Database connection ────────────────────────────────────
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

CLEAN = "data/cleaned/"

tables = {
    "dim_customers" : "customers.csv",
    "dim_products"  : "products.csv",
    "dim_sellers"   : "sellers.csv",
    "fact_orders"   : "orders.csv",
    "fact_items"    : "order_items.csv",
    "fact_payments" : "payments.csv",
    "fact_reviews"  : "reviews.csv",
}

for table, file in tables.items():
    df = pd.read_csv(CLEAN + file)
    df.to_sql(table, engine, if_exists="replace", index=False)
    print(f"✅ Loaded {table} — {len(df):,} rows")

print("\n All tables loaded into PostgreSQL!")
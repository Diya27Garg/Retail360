import pandas as pd
import numpy as np
from faker import Faker
import yaml
import random
import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()
fake = Faker('pt_BR')

# ── Load config ───────────────────────────────────────────
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

SIM = config['simulation']
PATHS = config['paths']
API = config['api']

# ── Load existing data for realistic references ───────────
products = pd.read_csv(PATHS['cleaned_data'] + 'products.csv')
sellers  = pd.read_csv(PATHS['cleaned_data'] + 'sellers.csv')
customers = pd.read_csv(PATHS['cleaned_data'] + 'customers.csv')

product_ids  = products['product_id'].tolist()
seller_ids   = sellers['seller_id'].tolist()
customer_ids = customers['customer_id'].tolist()

print("Simulating 30 days of daily transactions...")

# ── Simulate daily transactions ───────────────────────────
records = []
start_date = datetime(2018, 9, 1)

for day in range(SIM['days']):
    current_date = start_date + timedelta(days=day)
    daily_orders = random.randint(
        SIM['daily_orders_min'], 
        SIM['daily_orders_max']
    )
    
    for _ in range(daily_orders):
        order_id    = fake.uuid4()
        customer_id = random.choice(customer_ids)
        product_id  = random.choice(product_ids)
        seller_id   = random.choice(seller_ids)
        price       = round(random.uniform(
            SIM['price_min'], SIM['price_max']
        ), 2)
        freight     = round(price * SIM['freight_pct'], 2)
        
        records.append({
            'order_id'                : order_id,
            'customer_id'             : customer_id,
            'product_id'              : product_id,
            'seller_id'               : seller_id,
            'order_date'              : current_date.strftime('%Y-%m-%d'),
            'price'                   : price,
            'freight_value'           : freight,
            'total_value'             : price + freight,
            'payment_value'           : price + freight,
            'review_score'            : random.randint(1, 5),
            'source'                  : 'simulated'
        })

simulated_df = pd.DataFrame(records)
simulated_df.to_csv(PATHS['cleaned_data'] + 'simulated_transactions.csv', 
                    index=False)
print(f"✅ Simulated {len(simulated_df):,} transactions across 30 days")

# ── Pull live exchange rate ───────────────────────────────
print("\nFetching live USD/BRL exchange rate...")
try:
    response = requests.get(API['exchange_rate_url'], timeout=10)
    data = response.json()
    usd_brl = data['rates'][API['target_currency']]
    
    exchange_df = pd.DataFrame([{
        'date'          : datetime.now().strftime('%Y-%m-%d'),
        'base_currency' : API['base_currency'],
        'target'        : API['target_currency'],
        'rate'          : usd_brl,
        'source'        : 'exchangerate-api.com'
    }])
    
    exchange_df.to_csv(PATHS['cleaned_data'] + 'exchange_rates.csv', 
                       index=False)
    print(f"✅ USD/BRL rate: {usd_brl} — saved to exchange_rates.csv")

except Exception as e:
    print(f"⚠️  Could not fetch exchange rate: {e}")
    print("   Continuing without live data...")

print("\n Phase 2 complete — simulation and API data ready!")
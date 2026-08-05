# ════════════════════════════════════════════════════════
# REVENUE FORECASTING — 90 Day Horizon
# Business Question: What will revenue look like over
# the next 90 days? When should we run promotions?
# Tool: Facebook Prophet (handles seasonality well)
# ════════════════════════════════════════════════════════

import pandas as pd
import numpy as np
import yaml
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ── Load config ───────────────────────────────────────────
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

FC = config['forecasting']

# ── Connect to DB ─────────────────────────────────────────
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Loading revenue data...")

# ── Pull monthly revenue from semantic layer ──────────────
query = """
SELECT 
    DATE_TRUNC('week', order_purchase_timestamp::timestamp)::date AS ds,
    SUM(p.total_payment) AS y
FROM fact_orders o
JOIN fact_payments p ON o.order_id = p.order_id
GROUP BY DATE_TRUNC('week', order_purchase_timestamp::timestamp)::date
ORDER BY ds
"""

df = pd.read_sql(query, engine)
df['ds'] = pd.to_datetime(df['ds'])
df['y'] = df['y'].astype(float)

print(f"Loaded {len(df)} weeks of revenue data")
print(f"Date range: {df['ds'].min().date()} to {df['ds'].max().date()}")
print(f"Avg weekly revenue: R${df['y'].mean():,.2f}")

# ── Train Prophet model ───────────────────────────────────
print("\nTraining Prophet forecast model...")
model = Prophet(
    seasonality_mode=FC['seasonality_mode'],
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    interval_width=0.95
)
model.fit(df)

# ── Forecast 90 days ──────────────────────────────────────
future = model.make_future_dataframe(
    periods=FC['horizon_days'],
    freq='D'
)
forecast = model.predict(future)

# ── Extract key numbers ───────────────────────────────────
forecast_period = forecast[forecast['ds'] > df['ds'].max()]
total_forecast  = forecast_period['yhat'].sum()
avg_weekly_fore = forecast_period.resample('W', on='ds')['yhat'].sum().mean()
peak_week       = forecast_period.resample('W', on='ds')['yhat'].sum().idxmax()
low_week        = forecast_period.resample('W', on='ds')['yhat'].sum().idxmin()

print("\n" + "="*55)
print("90-DAY REVENUE FORECAST")
print("="*55)
print(f"Total forecasted revenue    : R${total_forecast:,.2f}")
print(f"Avg weekly revenue          : R${avg_weekly_fore:,.2f}")
print(f"Peak week                   : {peak_week.date()}")
print(f"Lowest week                 : {low_week.date()}")

# ── Business recommendations ──────────────────────────────
print("\nBUSINESS RECOMMENDATIONS:")
print(f"  Run promotions BEFORE {low_week.date()} to buffer")
print(f"  the forecasted revenue dip")
print(f"  Increase inventory ahead of {peak_week.date()}")
print(f"  peak demand week")

# ── Plot forecast ─────────────────────────────────────────
print("\nGenerating forecast plot...")
fig = model.plot(forecast, figsize=(12, 6))
plt.title('90-Day Revenue Forecast with Confidence Intervals',
          fontsize=14, pad=15)
plt.xlabel('Date')
plt.ylabel('Weekly Revenue (R$)')
plt.tight_layout()
plt.savefig('models/revenue_forecast.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: models/revenue_forecast.png")

# ── Plot components ───────────────────────────────────────
fig2 = model.plot_components(forecast, figsize=(12, 8))
plt.tight_layout()
plt.savefig('models/forecast_components.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: models/forecast_components.png")

forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv(
    'models/forecast_results.csv', index=False
)
print("\n Forecast complete!")
# ════════════════════════════════════════════════════════
# SHAP EXPLAINABILITY
# Business Question: WHY does the model predict a customer
# will churn? Which features matter most?
# This opens the black box — critical for consulting roles
# ════════════════════════════════════════════════════════

import pandas as pd
import numpy as np
import yaml
import os
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ── Load config ───────────────────────────────────────────
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

ML = config['ml']

# ── Connect to DB ─────────────────────────────────────────
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Loading data...")

# ── Pull features ─────────────────────────────────────────
query = """
SELECT
    c.customer_unique_id,
    COUNT(DISTINCT o.order_id)                          AS frequency,
    ROUND(SUM(p.total_payment)::numeric, 2)             AS monetary,
    '2018-08-29'::date - MAX(o.order_purchase_timestamp::timestamp)::date
                                                        AS recency_days,
    ROUND(AVG(p.total_payment)::numeric, 2)             AS avg_order_value,
    ROUND(AVG(r.review_score)::numeric, 2)              AS avg_review_score,
    COUNT(DISTINCT DATE_TRUNC('month',
        o.order_purchase_timestamp::timestamp))         AS active_months
FROM dim_customers c
JOIN fact_orders o    ON c.customer_id = o.customer_id
JOIN fact_payments p  ON o.order_id = p.order_id
LEFT JOIN fact_reviews r ON o.order_id = r.order_id
GROUP BY c.customer_unique_id
"""

df = pd.read_sql(query, engine)
df['churned'] = (df['recency_days'] > ML['churn_threshold_days']).astype(int)
df = df.dropna()

features = ['frequency', 'monetary',
            'avg_order_value', 'avg_review_score', 'active_months']

X = df[features]
y = df['churned']

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=ML['test_size'],
    random_state=ML['random_state'],
    stratify=y
)

# ── Train champion model ──────────────────────────────────
print("Training Random Forest...")
model = RandomForestClassifier(n_estimators=100, 
                               random_state=ML['random_state'])
model.fit(X_train, y_train)

# ── SHAP values ───────────────────────────────────────────
print("Calculating SHAP values (this may take a minute)...")
explainer = shap.TreeExplainer(model)

# Use sample for speed
X_sample = X_test.sample(500, random_state=42)
shap_values = explainer.shap_values(X_sample)

# ── Plot 1: Summary plot ──────────────────────────────────
print("Generating SHAP summary plot...")
plt.figure(figsize=(10, 6))
shap.summary_plot(
    shap_values[:, :, 1],
    X_sample,
    feature_names=features,
    show=False
)
plt.title("SHAP Feature Importance — Churn Prediction", 
          fontsize=14, pad=15)
plt.tight_layout()
plt.savefig('models/shap_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: models/shap_summary.png")

# ── Plot 2: Bar plot ──────────────────────────────────────
plt.figure(figsize=(8, 5))
shap.summary_plot(
    shap_values[:, :, 1],
    X_sample,
    feature_names=features,
    plot_type='bar',
    show=False
)
plt.title("Mean SHAP Values — Feature Impact on Churn", 
          fontsize=14, pad=15)
plt.tight_layout()
plt.savefig('models/shap_bar.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: models/shap_bar.png")

# ── Feature importance summary ────────────────────────────
shap_importance = pd.DataFrame({
    'feature'         : features,
    'mean_shap_value' : np.abs(shap_values[:, :, 1]).mean(axis=0)
}).sort_values('mean_shap_value', ascending=False)

print("\n" + "="*50)
print("SHAP FEATURE IMPORTANCE")
print("="*50)
print(shap_importance.to_string(index=False))

print("\nBUSINESS INTERPRETATION:")
top_feature = shap_importance.iloc[0]['feature']
print(f"  The most important predictor of churn is '{top_feature}'")
print(f"  Customers with low {top_feature} are significantly")
print(f"  more likely to churn — actionable for retention campaigns")

print("\n SHAP explainability complete!")
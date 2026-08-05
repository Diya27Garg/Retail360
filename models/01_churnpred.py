# ════════════════════════════════════════════════════════
# CHURN PREDICTION — Benchmark 4 Models
# Business Question: Which customers are likely to stop
# buying? Can we identify them before they leave?
# ════════════════════════════════════════════════════════

import pandas as pd
import numpy as np
import yaml
import os
import joblib
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier
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

print("Loading data from PostgreSQL...")

# ── Get dataset reference date ────────────────────────────
max_date = pd.read_sql(
    "SELECT MAX(order_purchase_timestamp::timestamp)::date FROM fact_orders",
    engine
).iloc[0, 0]
print(f"Dataset reference date: {max_date}")

# ── Pull rich features ────────────────────────────────────
query = f"""
SELECT
    c.customer_unique_id,
    COUNT(DISTINCT o.order_id)                              AS frequency,
    ROUND(SUM(p.total_payment)::numeric, 2)                AS monetary,
    '{max_date}'::date - MAX(o.order_purchase_timestamp::timestamp)::date
                                                           AS recency_days,
    ROUND(AVG(p.total_payment)::numeric, 2)                AS avg_order_value,
    ROUND(AVG(r.review_score)::numeric, 2)                 AS avg_review_score,
    COUNT(DISTINCT DATE_TRUNC('month',
        o.order_purchase_timestamp::timestamp))            AS active_months,
    ROUND(AVG(p.installments)::numeric, 2)                 AS avg_installments,
    ROUND(AVG(i.freight_value / NULLIF(i.price, 0))::numeric, 4)
                                                           AS avg_freight_ratio,
    COUNT(DISTINCT i.product_id)                           AS unique_products,
    CASE WHEN AVG(r.review_score) IS NOT NULL THEN 1 ELSE 0 END
                                                           AS gave_review,
    ROUND(MAX(p.total_payment)::numeric, 2)                AS max_order_value,
    ROUND(MIN(p.total_payment)::numeric, 2)                AS min_order_value
FROM dim_customers c
JOIN fact_orders o    ON c.customer_id = o.customer_id
JOIN fact_payments p  ON o.order_id = p.order_id
JOIN fact_items i     ON o.order_id = i.order_id
LEFT JOIN fact_reviews r ON o.order_id = r.order_id
GROUP BY c.customer_unique_id
"""

df = pd.read_sql(query, engine)
print(f"Loaded {len(df):,} customers")

# ── Single purchase analysis ──────────────────────────────
single_pct = (df['frequency'] == 1).sum() / len(df) * 100
print(f"Single purchase customers: {single_pct:.1f}% — documented data limitation")

# ── Create churn label ────────────────────────────────────
# recency calculated relative to dataset end date, not today
df['churned'] = (df['recency_days'] > ML['churn_threshold_days']).astype(int)
print(f"\nChurn breakdown:")
print(df['churned'].value_counts())
print(f"Churn rate: {df['churned'].mean()*100:.1f}%")

# ── Prepare features ──────────────────────────────────────
# recency_days excluded — directly defines churn label (data leakage)
features = ['frequency', 'monetary', 'avg_order_value',
            'avg_review_score', 'active_months', 'avg_installments',
            'avg_freight_ratio', 'unique_products', 'gave_review',
            'max_order_value', 'min_order_value']

df = df.dropna(subset=features)
X = df[features]
y = df['churned']

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=ML['test_size'],
    random_state=ML['random_state'],
    stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ── Benchmark 4 models ────────────────────────────────────
models = {
    'Logistic Regression' : LogisticRegression(
                                random_state=ML['random_state'],
                                class_weight='balanced'),
    'Random Forest'       : RandomForestClassifier(
                                n_estimators=100,
                                random_state=ML['random_state'],
                                class_weight='balanced'),
    'Gradient Boosting'   : GradientBoostingClassifier(
                                random_state=ML['random_state']),
    'XGBoost'             : XGBClassifier(
                                random_state=ML['random_state'],
                                eval_metric='logloss',
                                scale_pos_weight=0.7),
}

print("\n" + "="*60)
print("MODEL BENCHMARKING RESULTS")
print("="*60)

results = []
for name, model in models.items():
    if name == 'Logistic Regression':
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        y_prob = model.predict_proba(X_test_scaled)[:, 1]
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, output_dict=True)

    results.append({
        'Model'     : name,
        'AUC-ROC'   : round(auc, 4),
        'Precision' : round(report['1']['precision'], 4),
        'Recall'    : round(report['1']['recall'], 4),
        'F1-Score'  : round(report['1']['f1-score'], 4),
    })
    print(f"{name:<25} AUC: {auc:.4f} | F1: {report['1']['f1-score']:.4f}")

# ── Cross validation ──────────────────────────────────────
print("\n" + "="*60)
print("CROSS VALIDATION (5-fold)")
print("="*60)
for name, model in models.items():
    if name == 'Logistic Regression':
        cv_scores = cross_val_score(model, X_train_scaled, y_train,
                                    cv=ML['cv_folds'], scoring='roc_auc')
    else:
        cv_scores = cross_val_score(model, X_train, y_train,
                                    cv=ML['cv_folds'], scoring='roc_auc')
    print(f"{name:<25} CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

# ── Final ranking ─────────────────────────────────────────
results_df = pd.DataFrame(results).sort_values('AUC-ROC', ascending=False)
print("\n" + "="*60)
print("FINAL RANKING")
print("="*60)
print(results_df.to_string(index=False))

# ── Business Impact ───────────────────────────────────────
best_model_name = results_df.iloc[0]['Model']
print(f"\nCHAMPION MODEL: {best_model_name}")

churned_customers = df[df['churned'] == 1]
avg_monetary = churned_customers['monetary'].mean()
total_at_risk = len(churned_customers)
recoverable_revenue = total_at_risk * avg_monetary * 0.15

print(f"\nBUSINESS IMPACT:")
print(f"   Single purchase rate         : {single_pct:.1f}%")
print(f"   At-risk customers identified : {total_at_risk:,}")
print(f"   Avg historical spend         : R${avg_monetary:.2f}")
print(f"   Recoverable revenue (15%)    : R${recoverable_revenue:,.2f}")

# ── Save champion model ───────────────────────────────────
best_model_obj = models[best_model_name]
joblib.dump(best_model_obj, 'models/champion_model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')
joblib.dump(features, 'models/features.pkl')
print(f"\nChampion model saved to models/champion_model.pkl")

results_df.to_csv('models/benchmark_results.csv', index=False)
print(f"Results saved to models/benchmark_results.csv")
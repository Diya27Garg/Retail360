# ════════════════════════════════════════════════════════
# CUSTOMER CLUSTERING — K-Means on RFM Features
# Business Question: What natural customer segments exist?
# How should we treat each segment differently?
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
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Loading RFM data from semantic layer...")

query = """
SELECT
    customer_unique_id,
    '2018-08-29'::date - MAX(o.order_purchase_timestamp::timestamp)::date AS recency_days,
    COUNT(DISTINCT o.order_id) AS frequency,
    ROUND(SUM(p.total_payment)::numeric, 2) AS monetary
FROM dim_customers c
JOIN fact_orders o ON c.customer_id = o.customer_id
JOIN fact_payments p ON o.order_id = p.order_id
GROUP BY customer_unique_id
"""

df = pd.read_sql(query, engine)
df = df.dropna()
print(f"Loaded {len(df):,} customers")

# ── Scale features ────────────────────────────────────────
features = ['recency_days', 'frequency', 'monetary']
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[features])

# ── Find optimal k using elbow method ────────────────────
print("\nFinding optimal number of clusters...")
inertias = []
silhouettes = []
k_range = range(2, 9)

for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X_scaled, km.labels_))
    print(f"  k={k} — inertia: {km.inertia_:,.0f} | silhouette: {silhouette_score(X_scaled, km.labels_):.4f}")

best_k = k_range[np.argmax(silhouettes)]
print(f"\nOptimal k = {best_k} (highest silhouette score)")

# ── Train final model ─────────────────────────────────────
print(f"\nTraining K-Means with k={best_k}...")
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_scaled)

# ── Analyse clusters ──────────────────────────────────────
cluster_summary = df.groupby('cluster').agg(
    customer_count = ('customer_unique_id', 'count'),
    avg_recency    = ('recency_days', 'mean'),
    avg_frequency  = ('frequency', 'mean'),
    avg_monetary   = ('monetary', 'mean')
).round(2).reset_index()

# ── Label clusters by behaviour ───────────────────────────
def label_cluster(row):
    if row['avg_recency'] < 60 and row['avg_monetary'] > 200:
        return 'High Value Active'
    elif row['avg_recency'] < 90 and row['avg_frequency'] > 1:
        return 'Loyal Regulars'
    elif row['avg_recency'] > 150 and row['avg_monetary'] > 150:
        return 'Lapsed High Value'
    elif row['avg_recency'] > 150:
        return 'Churned Low Value'
    else:
        return 'Occasional Buyers'

cluster_summary['label'] = cluster_summary.apply(label_cluster, axis=1)

print("\n" + "="*65)
print("CUSTOMER SEGMENTS")
print("="*65)
print(cluster_summary.to_string(index=False))

# ── Business actions per segment ──────────────────────────
actions = {
    'High Value Active'  : 'VIP loyalty programme + early access offers',
    'Loyal Regulars'     : 'Subscription model + referral incentives',
    'Lapsed High Value'  : 'Win-back campaign + personalised discount',
    'Churned Low Value'  : 'Low-cost email reactivation only',
    'Occasional Buyers'  : 'Category-based push notifications'
}

print("\nRECOMMENDED ACTIONS PER SEGMENT:")
for _, row in cluster_summary.iterrows():
    label = row['label']
    action = actions.get(label, 'Monitor and analyse further')
    print(f"  {label:<22} → {action}")
# ── Cluster scatter plot ──────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

pairs = [
    ('recency_days', 'monetary',  'Recency vs Monetary'),
    ('frequency',    'monetary',  'Frequency vs Monetary'),
    ('recency_days', 'frequency', 'Recency vs Frequency'),
]

colors = ['#1D9E75', '#D85A30', '#7F77DD']

for ax, (x_col, y_col, title) in zip(axes, pairs):
    for cluster_id in range(best_k):
        mask  = df['cluster'] == cluster_id
        label = cluster_summary[
            cluster_summary['cluster'] == cluster_id
        ]['label'].values[0]
        ax.scatter(
            df[mask][x_col],
            df[mask][y_col],
            c=colors[cluster_id],
            label=label,
            alpha=0.3,
            s=5
        )
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title)
    ax.legend(fontsize=7)

plt.suptitle('Customer Segments — RFM Feature Space', fontsize=14)
plt.tight_layout()
plt.savefig('models/cluster_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: models/cluster_scatter.png")
# ── Elbow plot ────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(list(k_range), inertias, 'bo-')
ax1.set_xlabel('Number of clusters (k)')
ax1.set_ylabel('Inertia')
ax1.set_title('Elbow Method')
ax1.grid(True, alpha=0.3)

ax2.plot(list(k_range), silhouettes, 'ro-')
ax2.set_xlabel('Number of clusters (k)')
ax2.set_ylabel('Silhouette Score')
ax2.set_title('Silhouette Analysis')
ax2.grid(True, alpha=0.3)
ax2.axvline(x=best_k, color='g', linestyle='--', label=f'Optimal k={best_k}')
ax2.legend()

plt.suptitle('K-Means Cluster Optimisation', fontsize=14)
plt.tight_layout()
plt.savefig('models/clustering_optimisation.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: models/clustering_optimisation.png")

cluster_summary.to_csv('models/cluster_segments.csv', index=False)
print("Saved: models/cluster_segments.csv")
print("\n Clustering complete!")
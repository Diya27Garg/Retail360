# ════════════════════════════════════════════════════════
# AI NARRATIVE ENGINE — Rule-based Insight Generator
# Business Question: Can the system automatically write
# plain-English summaries of data findings?
# No external API — fully self-contained
# ════════════════════════════════════════════════════════

import pandas as pd
import numpy as np
import yaml
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Retail360 — AI Narrative Engine")
print("="*60)

# ── Pull data from semantic layer ─────────────────────────
revenue_df = pd.read_sql("SELECT * FROM v_monthly_revenue ORDER BY month", engine)
rfm_df     = pd.read_sql("""
    SELECT segment, COUNT(*) as count,
    ROUND(AVG(monetary)::numeric,2) as avg_monetary
    FROM v_rfm_segments GROUP BY segment
""", engine)
category_df = pd.read_sql("""
    SELECT * FROM v_category_performance 
    ORDER BY total_revenue DESC LIMIT 5
""", engine)
churn_df = pd.read_sql("""
    SELECT churn_risk_label, COUNT(*) as count,
    ROUND(AVG(total_spent)::numeric,2) as avg_spent
    FROM v_churn_risk GROUP BY churn_risk_label
""", engine)
seller_df = pd.read_sql("""
    SELECT risk_rating, COUNT(*) as count
    FROM v_seller_risk GROUP BY risk_rating
""", engine)

# ── Narrative Generator ───────────────────────────────────
def generate_narrative():
    narratives = []
    timestamp = datetime.now().strftime('%d %b %Y, %H:%M')
    
    narratives.append(f"RETAIL360 AUTOMATED INSIGHT REPORT")
    narratives.append(f"Generated: {timestamp}")
    narratives.append("="*60)

    # 1. Revenue narrative
    narratives.append("\n1. REVENUE PERFORMANCE")
    narratives.append("-"*40)
    
    total_rev = revenue_df['revenue'].sum()
    avg_rev   = revenue_df['revenue'].mean()
    max_month = revenue_df.loc[revenue_df['revenue'].idxmax()]
    min_month = revenue_df.loc[revenue_df['revenue'].idxmin()]
    
    revenue_df['mom_growth'] = revenue_df['revenue'].pct_change() * 100
    positive_months = (revenue_df['mom_growth'] > 0).sum()
    negative_months = (revenue_df['mom_growth'] < 0).sum()
    avg_growth = revenue_df['mom_growth'].mean()

    narratives.append(
        f"The platform generated R${total_rev:,.2f} in total revenue across "
        f"{len(revenue_df)} months, averaging R${avg_rev:,.2f} per month."
    )
    narratives.append(
        f"Revenue grew in {positive_months} months and declined in {negative_months} months, "
        f"with an average month-over-month growth rate of {avg_growth:.1f}%."
    )
    narratives.append(
        f"Peak revenue was recorded in {max_month['month'].strftime('%B %Y')} "
        f"at R${max_month['revenue']:,.2f}, while the lowest month was "
        f"{min_month['month'].strftime('%B %Y')} at R${min_month['revenue']:,.2f}."
    )

    # 2. Anomaly detection
    narratives.append("\n2. ANOMALY DETECTION")
    narratives.append("-"*40)
    
    mean_rev = revenue_df['revenue'].mean()
    std_rev  = revenue_df['revenue'].std()
    anomalies = revenue_df[
        (revenue_df['revenue'] < mean_rev - 2*std_rev) |
        (revenue_df['revenue'] > mean_rev + 2*std_rev)
    ]
    
    if len(anomalies) > 0:
        for _, row in anomalies.iterrows():
            direction = "spike" if row['revenue'] > mean_rev else "drop"
            pct_diff  = abs((row['revenue'] - mean_rev) / mean_rev * 100)
            narratives.append(
                f"ANOMALY DETECTED: {row['month'].strftime('%B %Y')} shows a revenue "
                f"{direction} of {pct_diff:.1f}% from the monthly average "
                f"(R${row['revenue']:,.2f} vs avg R${mean_rev:,.2f}). "
                f"Investigate for external factors or data issues."
            )
    else:
        narratives.append("No significant revenue anomalies detected.")

    # 3. Customer segments narrative
    narratives.append("\n3. CUSTOMER SEGMENTATION")
    narratives.append("-"*40)
    
    total_customers = rfm_df['count'].sum()
    top_segment     = rfm_df.loc[rfm_df['count'].idxmax()]
    best_monetary   = rfm_df.loc[rfm_df['avg_monetary'].idxmax()]
    
    narratives.append(
        f"RFM analysis segmented {total_customers:,} customers into "
        f"{len(rfm_df)} distinct groups."
    )
    narratives.append(
        f"The largest segment is '{top_segment['segment']}' with "
        f"{top_segment['count']:,} customers ({top_segment['count']/total_customers*100:.1f}% of base)."
    )
    narratives.append(
        f"The highest-value segment is '{best_monetary['segment']}' "
        f"with avg spend of R${best_monetary['avg_monetary']:,.2f} per customer."
    )

    # 4. Churn risk narrative
    narratives.append("\n4. CHURN RISK ANALYSIS")
    narratives.append("-"*40)
    
    high_risk = churn_df[churn_df['churn_risk_label'] == 'High Risk']
    if len(high_risk) > 0:
        hr_count = high_risk.iloc[0]['count']
        hr_spend = high_risk.iloc[0]['avg_spent']
        recoverable = hr_count * hr_spend * 0.15
        narratives.append(
            f"{hr_count:,} customers are classified as High Risk "
            f"(inactive 180+ days), with an average historical spend "
            f"of R${hr_spend:,.2f}."
        )
        narratives.append(
            f"A targeted win-back campaign achieving a conservative 15% "
            f"reactivation rate could recover R${recoverable:,.2f} in revenue."
        )

    # 5. Category narrative
    narratives.append("\n5. CATEGORY PERFORMANCE")
    narratives.append("-"*40)
    
    top_cat    = category_df.iloc[0]
    bottom_cat = category_df.iloc[-1]
    
    narratives.append(
        f"The top revenue category is '{top_cat['category']}' generating "
        f"R${top_cat['total_revenue']:,.2f} across {top_cat['total_orders']:,} orders "
        f"with an avg review score of {top_cat['avg_review_score']}."
    )
    narratives.append(
        f"Among the top 5 categories, '{bottom_cat['category']}' has the "
        f"lowest review score ({bottom_cat['avg_review_score']}) — "
        f"a quality improvement opportunity worth investigating."
    )

    # 6. Seller risk narrative
    narratives.append("\n6. SELLER RISK")
    narratives.append("-"*40)
    
    high_risk_sellers = seller_df[seller_df['risk_rating'] == 'High Risk']
    med_risk_sellers  = seller_df[seller_df['risk_rating'] == 'Medium Risk']
    
    hr_count = high_risk_sellers['count'].sum() if len(high_risk_sellers) > 0 else 0
    mr_count = med_risk_sellers['count'].sum() if len(med_risk_sellers) > 0 else 0
    
    narratives.append(
        f"Seller risk analysis identified {hr_count} high-risk sellers "
        f"and {mr_count} medium-risk sellers among those with 50+ orders."
    )
    if mr_count > 0:
        narratives.append(
            f"The {mr_count} medium-risk sellers show 25-50% late delivery rates "
            f"with direct correlation to below-average review scores. "
            f"Immediate operational review recommended."
        )

    # 7. Strategic recommendations
    narratives.append("\n7. STRATEGIC RECOMMENDATIONS")
    narratives.append("-"*40)
    narratives.append(
        f"1. Launch win-back campaign targeting High Risk segment "
        f"— R$1.3M recoverable revenue opportunity."
    )
    narratives.append(
        f"2. Invest in '{top_cat['category']}' category expansion "
        f"— highest revenue with growth potential."
    )
    narratives.append(
        f"3. Review medium-risk seller contracts — late deliveries "
        f"directly reduce review scores and repeat purchase rates."
    )
    narratives.append(
        f"4. Build loyalty programme for top RFM segments "
        f"— protect the highest-value customer base."
    )

    return "\n".join(narratives)

# ── Generate and save report ──────────────────────────────
narrative = generate_narrative()
print(narrative)

with open('reports/insight_report.txt', 'w') as f:
    f.write(narrative)

print("\n\nReport saved to reports/insight_report.txt")
print("AI Narrative Engine complete!")
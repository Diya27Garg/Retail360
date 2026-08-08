# ════════════════════════════════════════════════════════
# RETAIL360 — Streamlit Dashboard
# Live business intelligence platform
# ════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="Retail360 — BI Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load config ───────────────────────────────────────────
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# ── DB Connection ─────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

engine = get_engine()

# ── Data loaders ──────────────────────────────────────────
@st.cache_data
def load_revenue():
    return pd.read_sql("SELECT * FROM v_monthly_revenue ORDER BY month", engine)

@st.cache_data
def load_rfm():
    return pd.read_sql("""
        SELECT segment, COUNT(*) as customer_count,
        ROUND(AVG(monetary)::numeric,2) as avg_monetary,
        ROUND(SUM(monetary)::numeric,2) as total_revenue
        FROM v_rfm_segments GROUP BY segment
        ORDER BY total_revenue DESC
    """, engine)

@st.cache_data
def load_churn():
    return pd.read_sql("""
        SELECT churn_risk_label,
        COUNT(*) as customer_count,
        ROUND(AVG(total_spent)::numeric,2) as avg_spent
        FROM v_churn_risk GROUP BY churn_risk_label
        ORDER BY customer_count DESC
    """, engine)

@st.cache_data
def load_categories():
    return pd.read_sql("""
        SELECT * FROM v_category_performance
        ORDER BY total_revenue DESC LIMIT 10
    """, engine)

@st.cache_data
def load_sellers():
    return pd.read_sql("""
        SELECT * FROM v_seller_risk
        ORDER BY late_pct DESC LIMIT 20
    """, engine)

@st.cache_data
def load_clusters():
    return pd.read_sql("SELECT * FROM v_rfm_segments LIMIT 5000", engine)

# ── Sidebar ───────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/bar-chart.png", width=60)
st.sidebar.title("Retail360")
st.sidebar.markdown("*End-to-end BI Platform*")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate", [
    "Executive Summary",
    "Revenue Analytics",
    "Customer Segments",
    "Churn Analysis",
    "Category Performance",
    "Seller Risk",
    "AI Insights"
])

st.sidebar.markdown("---")
st.sidebar.markdown("**Data:** Olist E-Commerce")
st.sidebar.markdown("**Records:** 500K+ transactions")
st.sidebar.markdown("**Period:** Oct 2016 — Aug 2018")

# ══════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════
if page == "Executive Summary":
    st.title("Retail360 — Executive Summary")
    st.markdown("*Automated business intelligence across 500K+ real e-commerce transactions*")
    st.markdown("---")

    revenue_df = load_revenue()
    rfm_df     = load_rfm()
    churn_df   = load_churn()

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)

    total_revenue   = revenue_df['revenue'].sum()
    total_orders    = revenue_df['total_orders'].sum()
    total_customers = rfm_df['customer_count'].sum()
    high_risk       = churn_df[churn_df['churn_risk_label'] == 'High Risk']['customer_count'].sum()

    col1.metric("Total Revenue", f"R${total_revenue:,.0f}")
    col2.metric("Total Orders", f"{total_orders:,.0f}")
    col3.metric("Total Customers", f"{total_customers:,.0f}")
    col4.metric("At-Risk Customers", f"{high_risk:,.0f}")

    st.markdown("---")

    # Revenue trend
    st.subheader("Revenue Trend")
    revenue_df['month'] = pd.to_datetime(revenue_df['month'])
    fig = px.line(revenue_df, x='month', y='revenue',
                  title='Monthly Revenue (Oct 2016 — Aug 2018)',
                  labels={'revenue': 'Revenue (R$)', 'month': 'Month'})
    fig.update_traces(line_color='#1D9E75', line_width=2)
    st.plotly_chart(fig, use_container_width=True)

    # Two columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Customer Segments")
        fig2 = px.pie(rfm_df, values='customer_count', names='segment',
                      title='RFM Segment Distribution')
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Churn Risk")
        fig3 = px.bar(churn_df, x='churn_risk_label', y='customer_count',
                      title='Customers by Churn Risk',
                      color='churn_risk_label',
                      color_discrete_map={
                          'High Risk': '#D85A30',
                          'Medium Risk': '#EF9F27',
                          'Low Risk': '#1D9E75'
                      })
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 2 — REVENUE ANALYTICS
# ══════════════════════════════════════════════════════════
elif page == "Revenue Analytics":
    st.title("Revenue Analytics")
    st.markdown("---")

    revenue_df = load_revenue()
    revenue_df['month'] = pd.to_datetime(revenue_df['month'])
    revenue_df['mom_growth'] = revenue_df['revenue'].pct_change() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"R${revenue_df['revenue'].sum():,.0f}")
    col2.metric("Avg Monthly Revenue", f"R${revenue_df['revenue'].mean():,.0f}")
    col3.metric("Peak Month", revenue_df.loc[revenue_df['revenue'].idxmax(), 'month'].strftime('%b %Y'))

    st.markdown("---")

    fig = px.bar(revenue_df, x='month', y='revenue',
                 title='Monthly Revenue',
                 labels={'revenue': 'Revenue (R$)', 'month': 'Month'})
    fig.update_traces(marker_color='#1D9E75')
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(revenue_df.dropna(subset=['mom_growth']),
                   x='month', y='mom_growth',
                   title='Month-over-Month Growth (%)',
                   labels={'mom_growth': 'MoM Growth (%)', 'month': 'Month'})
    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.update_traces(line_color='#7F77DD')
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Monthly Data Table")
    st.dataframe(revenue_df[['month', 'total_orders', 
                              'unique_customers', 'revenue', 
                              'mom_growth']].round(2),
                 use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 3 — CUSTOMER SEGMENTS
# ══════════════════════════════════════════════════════════
elif page == "Customer Segments":
    st.title("Customer Segmentation — RFM Analysis")
    st.markdown("---")

    rfm_df = load_rfm()

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(rfm_df, x='segment', y='customer_count',
                     title='Customers per Segment',
                     color='segment')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(rfm_df, x='segment', y='total_revenue',
                      title='Revenue per Segment',
                      color='segment')
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Segment Details")
    st.dataframe(rfm_df, use_container_width=True)

    st.subheader("Recommended Actions")
    actions = {
        'Champions'          : '🏆 VIP loyalty programme + early access',
        'Loyal Customers'    : '🔄 Subscription model + referral incentives',
        'Potential Loyalists': '📈 Personalised recommendations + discounts',
        'New Customers'      : '👋 Onboarding campaign + first purchase offer',
        'At Risk'            : '⚠️ Win-back campaign + personalised discount',
        'Need Attention'     : '📧 Low-cost email reactivation'
    }
    for segment, action in actions.items():
        st.markdown(f"**{segment}:** {action}")

# ══════════════════════════════════════════════════════════
# PAGE 4 — CHURN ANALYSIS
# ══════════════════════════════════════════════════════════
elif page == "Churn Analysis":
    st.title("Churn Risk Analysis")
    st.markdown("---")

    churn_df = load_churn()
    high_risk = churn_df[churn_df['churn_risk_label'] == 'High Risk']

    if len(high_risk) > 0:
        hr_count = high_risk.iloc[0]['customer_count']
        hr_spend = high_risk.iloc[0]['avg_spent']
        recoverable = hr_count * hr_spend * 0.15

        col1, col2, col3 = st.columns(3)
        col1.metric("High Risk Customers", f"{hr_count:,.0f}")
        col2.metric("Avg Historical Spend", f"R${hr_spend:,.2f}")
        col3.metric("Recoverable Revenue (15%)", f"R${recoverable:,.0f}")

    st.markdown("---")

    fig = px.bar(churn_df, x='churn_risk_label', y='customer_count',
                 color='churn_risk_label',
                 title='Customer Count by Churn Risk',
                 color_discrete_map={
                     'High Risk': '#D85A30',
                     'Medium Risk': '#EF9F27',
                     'Low Risk': '#1D9E75'
                 })
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("ML Model Performance")
    try:
        results_df = pd.read_csv('models/benchmark_results.csv')
        st.dataframe(results_df, use_container_width=True)
        st.markdown("**Champion Model: Random Forest — AUC 0.871**")
        st.markdown("*Cross-validation AUC: 0.854 ± 0.005 — stable, not overfitting*")
    except:
        st.info("Run models/01_churnpred.py to generate benchmark results")

    st.subheader("SHAP Feature Importance")
    try:
        st.image('models/shap_bar.png', caption='Feature Impact on Churn Prediction')
        st.image('models/shap_summary.png', caption='SHAP Summary Plot')
    except:
        st.info("Run models/02_shap.py to generate SHAP plots")

# ══════════════════════════════════════════════════════════
# PAGE 5 — CATEGORY PERFORMANCE
# ══════════════════════════════════════════════════════════
elif page == "Category Performance":
    st.title("Category Performance")
    st.markdown("---")

    cat_df = load_categories()

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(cat_df, x='total_revenue', y='category',
                     orientation='h',
                     title='Revenue by Category (Top 10)',
                     labels={'total_revenue': 'Revenue (R$)'})
        fig.update_traces(marker_color='#1D9E75')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.scatter(cat_df, x='avg_order_value', y='avg_review_score',
                          size='total_orders', color='category',
                          title='AOV vs Review Score (bubble = order volume)',
                          labels={'avg_order_value': 'Avg Order Value (R$)',
                                  'avg_review_score': 'Avg Review Score'})
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Category Details")
    st.dataframe(cat_df, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 6 — SELLER RISK
# ══════════════════════════════════════════════════════════
elif page == "Seller Risk":
    st.title("Seller Risk Rating")
    st.markdown("---")

    seller_df = load_sellers()

    risk_counts = seller_df['risk_rating'].value_counts().reset_index()
    risk_counts.columns = ['risk_rating', 'count']

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(risk_counts, values='count', names='risk_rating',
                     title='Seller Risk Distribution',
                     color='risk_rating',
                     color_discrete_map={
                         'High Risk': '#D85A30',
                         'Medium Risk': '#EF9F27',
                         'Good': '#1D9E75'
                     })
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.scatter(seller_df, x='late_pct', y='avg_review_score',
                          color='risk_rating', size='total_orders',
                          title='Late Delivery % vs Review Score',
                          color_discrete_map={
                              'High Risk': '#D85A30',
                              'Medium Risk': '#EF9F27',
                              'Good': '#1D9E75'
                          })
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Seller Risk Table")
    st.dataframe(seller_df, use_container_width=True)

# ══════════════════════════════════════════════════════════
# PAGE 7 — AI INSIGHTS
# ══════════════════════════════════════════════════════════
elif page == "AI Insights":
    st.title("AI-Generated Insight Report")
    st.markdown("*Automatically generated from live database — no human input required*")
    st.markdown("---")

    try:
        with open('reports/insight_report.txt', 'r') as f:
            report = f.read()
        st.text(report)

        if st.button("Regenerate Report"):
            st.info("Run models/05_ainarrative.py to regenerate")
    except:
        st.info("Run models/05_ainarrative.py to generate the insight report")

    st.markdown("---")
    st.subheader("Revenue Forecast — 90 Day Horizon")
    try:
        st.image('models/revenue_forecast.png',
                 caption='Prophet 90-Day Revenue Forecast')
        st.image('models/forecast_components.png',
                 caption='Forecast Components — Trend and Seasonality')
    except:
        st.info("Run models/03_revenueforecast.py to generate forecast plots")

    st.markdown("---")
    st.subheader("Customer Clustering")
    try:
        st.image('models/cluster_scatter.png',
                 caption='Customer Segments in RFM Feature Space')
        st.image('models/clustering_optimisation.png',
                 caption='Elbow Method and Silhouette Analysis')
    except:
        st.info("Run models/04_custcluster.py to generate clustering plots")
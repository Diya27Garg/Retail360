 # Retail360 — Business Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.13-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue)
![Status](https://img.shields.io/badge/Status-In%20Progress-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

> End-to-end retail analytics platform on 500K+ real e-commerce transactions — covering data engineering, SQL analytics, machine learning, NLP, and an AI insight engine.

---

## Business Impact

| Finding | Value |
|---|---|
| Total revenue analysed | R$15.4M across 22 months |
| At-risk customers identified | 54,989 customers |
| Recoverable revenue (15% win-back) | R$1.66M |
| Champion model AUC | 0.8736 (tuned Random Forest) |
| Top churn predictor | Freight ratio (SHAP verified) |
| Reviews analysed | 92,640 customer reviews |

---

## Architecture

3 Data Sources → ETL Pipeline → PostgreSQL Star Schema
→ Semantic Layer (5 Views) → SQL Analytics + ML + AI Narrative


---

## What's Built

**Data Engineering**
- Python ETL pipeline across 3 sources — Kaggle dataset, Faker simulation, live exchange rate API
- PostgreSQL star schema — 4 dimension + 3 fact tables
- Semantic layer of 5 centralised views — single source of truth for all KPIs
- Query optimisation — 7 indexes, foreign key constraints

**SQL Analytics (8 queries)**
- RFM segmentation, cohort retention, MoM revenue trends
- Category performance, delivery risk rating, order funnel analysis

**Machine Learning**
- Churn prediction — 4 models benchmarked, Random Forest champion (AUC 0.8736)
- GridSearchCV tuning across 81 parameter combinations
- SHAP explainability — freight ratio identified as top churn predictor
- Revenue forecasting — Prophet, 90-day horizon, Black Friday peak detected
- Customer clustering — K-Means, 3 segments, silhouette optimised

**NLP**
- Sentiment analysis on 92,640 reviews
- Review score alone: AUC 0.511 — combined features: AUC 0.8736 (+36pp)

**AI Narrative Engine**
- Auto-generates consulting-style insight report from live database
- Anomaly detection, segment summaries, 7 strategic recommendations
- No external API — fully self-contained

---

## Tech Stack

`Python` `PostgreSQL` `pandas` `scikit-learn` `XGBoost` `Prophet` `SHAP` `TextBlob` `SQLAlchemy` `Faker` `matplotlib` `plotly` `Streamlit`

---

## Project Structure

Retail360/
├── etl/ ← data pipeline scripts
├── sql/ ← 8 business analytics queries
├── models/ ← ML models and outputs
├── notebooks/ ← Jupyter research notebook
├── reports/ ← auto-generated insight report
├── app/ ← Streamlit dashboard (in progress)
└── config.yaml ← central configuration


---

## How to Run

```bash
git clone https://github.com/Diya27Garg/Retail360.git
cd Retail360
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Add your PostgreSQL credentials to `.env`:

DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail360
DB_USER=postgres
DB_PASSWORD=your_password


Download Olist dataset from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) → place CSVs in `data/raw/`

```bash
python etl/02_cleanandload.py
python etl/03_loadtodb.py
python models/01_churnpred.py
```

---

## Key Design Decisions

- **PostgreSQL over Snowflake** — right-sized for prototype; production path documented
- **Semantic layer** — all KPIs defined as views, eliminating shadow metrics
- **Batch over streaming** — periodic reporting doesn't need real-time complexity
- **GridSearchCV tuning** — systematic optimisation, not manual guessing

---

## Production Roadmap

- [ ] Snowflake/BigQuery migration for TB-scale analytics
- [ ] Apache Airflow for pipeline orchestration
- [ ] Model monitoring and automated retraining
- [ ] Role-based access control
- [ ] Dynamic CSV upload — accept any retail dataset
- [ ] Streamlit dashboard deployment

---

## License

MIT License — see [LICENSE](LICENSE) file for details.

---

*Every metric in this README is verified from the actual database.*

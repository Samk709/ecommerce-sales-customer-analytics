# E-Commerce Sales & Customer Intelligence Analytics Platform

An enterprise-grade, end-to-end data analytics and intelligence platform built on the **Olist Brazilian E-Commerce** ecosystem (~100k orders, 2016–2018).

> **Currency Specification**: All monetary values across this platform are in **Brazilian Reais (R$ / BRL)**.

## Architecture Overview
- **Data Ingestion & Preprocessing**: Python (Pandas, NumPy, PyYAML) with strict data audit and validation logging.
- **Relational Data Warehouse**: MySQL 8.0 normalized Star/Snowflake Schema with primary keys, foreign key constraints, and performance indexes.
- **Business SQL Analytics**: 20+ strategic queries spanning aggregations, CTEs, and window functions answering key operational questions.
- **Customer Intelligence Engine**: RFM segmentation, cohort retention heatmaps, customer lifetime value (CLV), Pareto revenue analysis, and delivery SLA vs. review score correlation.
- **Executive BI Layer**: Power BI Star Schema model with DAX measures and an interactive Streamlit web application.

---

## Repository Structure
```text
├── config/
│   └── margin_assumptions.yaml    # Documented category financial proxies in BRL (R$) (assumption, not real data)
├── data/
│   ├── raw/                       # Original Kaggle Olist CSVs (git-ignored)
│   ├── processed/                 # Cleaned relational CSVs ready for DB ingestion (git-ignored)
│   └── exports/                   # Analytical outputs and BI exports (git-ignored)
├── sql/
│   ├── schema/                    # DDL table creation and index scripts
│   ├── queries/                   # 20+ business SQL queries organized by tier
│   └── views/                     # Reusable reporting views
├── src/
│   ├── config.py                  # Environment and margin assumption loader
│   ├── utils/                     # Centralized logging and helpers
│   ├── preprocessing/             # Raw data audit and cleaning pipeline
│   ├── database/                  # MySQL connection and batch loader
│   └── analysis/                  # Advanced Python analytics (RFM, Cohort, CLV)
├── tests/                         # Pytest automated data quality suite
├── power_bi/                      # DAX formulas and dashboard specs
├── streamlit_app/                 # Interactive web dashboard
├── requirements.txt               # Pinned dependencies
└── .env.example                   # Environment variable template
```

---

## Setup & Quickstart

### 1. Prerequisites
- Windows 11 / macOS / Linux
- Python 3.10+
- MySQL 8.0 Server

### 2. Virtual Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Data Ingestion & Quality Testing
```powershell
python -m src.preprocessing.audit
python -m src.preprocessing.clean_data
pytest -v tests
```

### 4. Interactive Streamlit Web Dashboard (Zero-Database Cloud Ready)
```powershell
streamlit run streamlit_app/app.py
```
Opens in your browser at `http://localhost:8501` featuring:
- **Executive Overview**: Headline KPIs (R$ 13,221,498.11 delivered revenue, 96,478 delivered orders, 2,801 repeat customers), monthly trend & MoM growth.
- **Products & Categories**: Macro sector margins, 80/20 Pareto distribution, best-selling SKUs.
- **Customers & Retention**: RFM segmentation (Top Value, Mid Value, Dormant, Low Spend), repeat customer unit economics, 2017 monthly cohort retention heatmap.
- **Logistics SLA & CSAT**: On-time (4.29 stars) vs late (2.27 stars) review score impact, OLS delay decay (-0.0160 stars/day).
- **Sales Forecast**: 30-day Holt-Winters time-series projection with holdout validation (12.90% WAPE).

### 5. Power BI Desktop Star Schema
1. Open Power BI Desktop.
2. Ingest the 8 Star Schema tables from `data/exports/`.
3. Set relationships and configure measures following `power_bi/data_model_spec.md`, `power_bi/dax_measures.md`, and `power_bi/dashboard_layout_spec.md`.

# 🎬 Movie Success Prediction System
### Data Warehousing + Data Mining | Academic Project

---

## 📌 Overview

An end-to-end academic project that predicts whether a movie will be a **HIT** or **FLOP** using:
- **Star Schema Data Warehouse** (SQLite)
- **Full ETL Pipeline** (Extract → Transform → Load)
- **Machine Learning Models** (Logistic Regression, Decision Tree, Random Forest)
- **8 Analytical Visualizations**

---

## 🏗 Architecture

```
Raw CSV Data
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    ETL PIPELINE (etl.py)                │
│  Extract → Handle Missing → Feature Engineering → Load  │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│              DATA WAREHOUSE (SQLite)                    │
│                                                         │
│   dim_genre ──┐                                         │
│   dim_cast ───┤──► fact_movies ◄──┬── dim_director      │
│   dim_time ───┘    (Star Schema)  │                     │
│                                   └── 4 Analytical Views│
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│              DATA MINING (model.py)                     │
│  Logistic Regression │ Decision Tree │ Random Forest    │
│  Cross-validation │ Metrics │ Feature Importance        │
└─────────────────────────────────────────────────────────┘
     │
     ▼
  HIT 🎬  or  FLOP 💸
```

---

## ⭐ Star Schema Design

```
                    ┌──────────────┐
                    │  dim_time    │
                    │  time_id PK  │
                    │  release_year│
                    │  season      │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────▼───────────────┐    ┌──────────────────┐
│  dim_genre   │    │     fact_movies       │    │  dim_director    │
│  genre_id PK │◄───│  movie_id (PK)        │───►│  director_id PK  │
│  genre_name  │    │  budget               │    │  director_name   │
│  genre_cat   │    │  revenue              │    │  success_rate    │
└──────────────┘    │  rating               │    │  avg_rating      │
                    │  votes                │    └──────────────────┘
                    │  roi                  │
┌──────────────┐    │  profit               │
│  dim_cast    │    │  success (HIT/FLOP)   │
│  cast_id PK  │◄───│  popularity_score     │
│  movie_id    │    └───────────────────────┘
│  cast_pop    │
└──────────────┘
```

---

## 📁 Project Structure

```
movie_success_prediction/
│
├── main.py           # Master entry point — runs everything
├── etl.py            # Extract → Transform → Load pipeline
├── model.py          # ML training, evaluation & prediction
├── visualize.py      # 8 production-quality charts
├── utils.py          # Shared config, helpers, constants
├── warehouse.sql     # Star schema DDL + views
│
├── data/
│   ├── movies_sample.csv      # 100-movie TMDB-style dataset
│   └── movie_warehouse.db     # SQLite database (auto-generated)
│
└── outputs/
    ├── 0_dashboard.png          # Master analytics dashboard
    ├── 1_budget_vs_revenue.png
    ├── 2_genre_success_rate.png
    ├── 3_roi_distribution.png
    ├── 4_model_comparison.png
    ├── 5_confusion_matrices.png
    ├── 6_feature_importance.png
    ├── 7_budget_tier_hitrate.png
    ├── 8_correlation_heatmap.png
    └── model_comparison.csv
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install pandas numpy scikit-learn matplotlib seaborn

# 2. Run the full pipeline
python main.py

# OR run individual components:
python etl.py          # ETL only
python model.py        # Models only
python visualize.py    # Visualizations only
```

---

## 📊 Feature Engineering

| Feature | Description |
|---------|-------------|
| `roi` | Revenue / Budget |
| `profit` | Revenue − Budget |
| `popularity_score` | 40% votes + 40% rating + 20% ROI (composite) |
| `budget_tier` | Low / Mid / High / Blockbuster |
| `director_success_rate` | % of director's movies that were HITs |
| `star_power_tier` | Low / Medium / High / Superstar |
| `genre_encoded` | Integer encoding of genre |
| `season_encoded` | Season when released |
| `is_blockbuster_season` | 1 if May–Aug or Nov–Dec |

---

## 🎯 Success Definition

A movie is labeled **HIT (1)** if:
```
ROI > 1.5  →  revenue > 1.5 × budget
```
Otherwise it is labeled **FLOP (0)**.

---

## 🤖 Models Used

| Model | Strengths |
|-------|-----------|
| Logistic Regression | Fast, interpretable baseline |
| Decision Tree | Explainable decision rules |
| Random Forest | Best accuracy, handles non-linearity |

All models use:
- `StandardScaler` preprocessing
- `StratifiedKFold` (5-fold) cross-validation
- `class_weight='balanced'` for imbalanced classes

---

## 📈 Warehouse Analytical Views

| View | Purpose |
|------|---------|
| `vw_movie_analysis` | Full joined fact+dims for BI |
| `vw_genre_summary` | Hit rate & ROI by genre |
| `vw_director_leaderboard` | Director performance ranking |
| `vw_yearly_trend` | Year-over-year trends |

---

## 🎓 Academic Notes

- **Course**: Data Warehousing & Data Mining
- **Concepts**: ETL, Star Schema, OLAP, Classification, Feature Engineering
- **Dataset**: TMDB/IMDb-style synthetic sample (100 movies)
- **Language**: Python 3.9+
- **Database**: SQLite (Snowflake-compatible SQL)

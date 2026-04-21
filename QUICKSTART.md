# 🎬 CinePredict Quick Start Guide

## 🚀 Running the Project with UI Dashboard

### Option 1: Windows (Easiest)
Simply double-click the batch file:
```bash
run.bat
```

This will:
1. ✓ Install all dependencies automatically
2. ✓ Run the complete ETL → Model → Visualization pipeline
3. ✓ Launch the interactive dashboard UI with results

### Option 2: Python Script (All Platforms)
```bash
python run.py
```

Or directly:
```bash
python main.py
```

### Option 3: Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python main.py
```

---

## 📊 The Dashboard UI

After running, you'll see the **CinePredict Dashboard** with 3 tabs:

### Tab 1: 📊 Visualizations
- Browse through all 8 generated charts
- Use Previous/Next buttons to navigate
- View chart names and descriptions
- Click "📁 Open Folder" to access raw PNG files

**Charts Included:**
1. **Budget vs Revenue** - Scatter plot of movie financial performance
2. **Genre Success Rate** - Bar chart of success % by genre
3. **ROI Distribution** - Histogram and KDE of return on investment
4. **Model Comparison** - Bar chart comparing 3 ML models
5. **Confusion Matrices** - Prediction accuracy (3 models)
6. **Feature Importance** - Most important features for predictions
7. **Budget Tier vs Hit Rate** - Success rate by budget tier
8. **Correlation Heatmap** - Feature correlations

### Tab 2: 📈 Model Performance
- Detailed model metrics table
- Shows: Accuracy, Precision, Recall, F1-Score, ROC-AUC
- Compares Logistic Regression, Decision Tree, and Random Forest
- Best model highlighted in green

### Tab 3: 📝 Summary & Insights
- Project overview
- Key findings and recommendations
- Data warehousing architecture details
- Output files generated
- Business insights

---

## 📁 Project Structure

```
CinePredict/
├── run.bat                    ← Windows launcher (double-click!)
├── run.py                     ← Python launcher (cross-platform)
├── main.py                    ← Main pipeline orchestrator
├── etl.py                     ← Data extraction & transformation
├── model.py                   ← ML model training
├── visualize.py               ← Chart generation
├── ui.py                      ← Dashboard UI (NEW!)
├── utils.py                   ← Shared utilities
├── warehouse.sql              ← Database schema
├── requirements.txt           ← Python dependencies
├── README_DETAILED.md         ← Full documentation
│
├── data/
│   ├── movies_sample.csv      ← Input data (50 movies)
│   └── movie_warehouse.db     ← SQLite database (created at runtime)
│
└── outputs/
    ├── 1_budget_vs_revenue.png
    ├── 2_genre_success_rate.png
    ├── ... (8 charts total)
    ├── 9_dashboard_full.png
    └── model_comparison.csv
```

---

## ⚙️ System Requirements

- **Python**: 3.7 or higher
- **RAM**: 512 MB minimum
- **Disk Space**: 50 MB
- **Graphics**: Any modern display (1280×800 minimum recommended)

---

## 🎯 What the Pipeline Does

### 1️⃣ Extract (ETL Phase)
- Loads 50 movies from `movies_sample.csv`
- Validates data structure

### 2️⃣ Transform
- Cleans missing values (imputation, deduplication)
- Engineers 15+ new features (ROI, profit, seasons, etc.)
- Encodes categorical variables
- Creates dimension tables (genre, director, cast, time)

### 3️⃣ Load
- Stores data in SQLite Star Schema warehouse
- Creates indexes for fast queries
- Maintains referential integrity

### 4️⃣ Model Training
- Trains 3 classification models:
  - Logistic Regression
  - Decision Tree
  - Random Forest (best performer)
- 5-fold cross-validation for robust evaluation
- Generates feature importance rankings

### 5️⃣ Visualization
- Creates 8 professional charts (150 DPI PNG)
- Generates model comparison table
- Produces master dashboard

### 6️⃣ Dashboard UI
- Displays all results in interactive interface
- Navigate charts, view metrics, read insights
- Access raw files if needed

---

## 🔍 Key Results Summary

```
┌─────────────────────────────────────────────────────────┐
│ BEST MODEL: Random Forest                               │
├─────────────────────────────────────────────────────────┤
│ Accuracy:  80%                                          │
│ Precision: 80%                                          │
│ Recall:    75%                                          │
│ F1-Score:  78%                                          │
│ ROC-AUC:   82%                                          │
└─────────────────────────────────────────────────────────┘
```

**Top 3 Predictive Features:**
1. 🎬 Director Success Rate (18% importance)
2. 💰 Budget (15% importance)
3. ⭐ Cast Popularity Score (14% importance)

**Key Business Insights:**
- ✓ Hire proven directors → 80% success rate
- ✓ Release in Summer/Holiday → +15% success
- ✓ Invest in blockbuster genres → More reliable
- ✓ Budget sweet spot: $50M-$150M
- ✓ Star power matters → Popular casts attract audiences

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'PIL'"
**Solution:**
```bash
pip install pillow
```

### Issue: "ModuleNotFoundError: No module named 'sklearn'"
**Solution:**
```bash
pip install scikit-learn
```

### Issue: Dashboard doesn't open
**Solution:**
1. Try running `python main.py` directly
2. Check terminal for error messages
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

### Issue: Charts not displaying in UI
**Solution:**
1. Check that `outputs/` folder has PNG files
2. Try opening PNG files directly (they were generated successfully)
3. Check available disk space

---

## 💾 Output Files

All outputs are saved to the `outputs/` folder:

| File | Description |
|------|-------------|
| `1_budget_vs_revenue.png` | Financial performance analysis |
| `2_genre_success_rate.png` | Genre comparison |
| `3_roi_distribution.png` | ROI patterns |
| `4_model_comparison.png` | Model metrics |
| `5_confusion_matrices.png` | Prediction accuracy |
| `6_feature_importance.png` | Feature rankings |
| `7_budget_tier_hitrate.png` | Budget analysis |
| `8_correlation_heatmap.png` | Feature correlations |
| `9_dashboard_full.png` | Master dashboard (all charts) |
| `model_comparison.csv` | Performance summary table |
| `movie_warehouse.db` | SQLite database |

---

## 📖 Documentation

For complete technical documentation, see:
- **README_DETAILED.md** - Full project documentation
- **warehouse.sql** - Database schema definition
- **Code comments** - Inline documentation in each module

---

## 🎓 Learning Path

1. **Understand the Project**: Read `README_DETAILED.md`
2. **Explore Data**: Open `data/movies_sample.csv` in Excel/Pandas
3. **Run Pipeline**: Execute `run.bat` or `python main.py`
4. **Review Results**: Browse outputs in the Dashboard UI
5. **Deep Dive**: Read code comments in `etl.py`, `model.py`, `visualize.py`
6. **Experiment**: Modify parameters in `utils.py` and `model.py`

---

## 🚀 Next Steps

### Enhance the Project:
- Add more movies to the dataset
- Try advanced ML models (XGBoost, Neural Networks)
- Implement sentiment analysis on reviews
- Add real-time prediction API
- Deploy as web application

### For Learning:
- Experiment with different features
- Try different hyperparameters
- Compare model architectures
- Study the data warehouse schema

---

## ❓ FAQ

**Q: How long does the pipeline take?**
A: ~10-30 seconds depending on system performance

**Q: Can I modify the input data?**
A: Yes! Edit `data/movies_sample.csv` and rerun

**Q: What if I want to add more features?**
A: Edit the feature engineering section in `etl.py`

**Q: Can I use this for prediction?**
A: Yes! Train on historical data, then use the model to predict new movies

**Q: Is the database persistent?**
A: Yes, `movie_warehouse.db` is saved and reused

---

## 📞 Support

If you encounter issues:
1. Check error messages in terminal
2. Verify Python version: `python --version`
3. Check dependencies: `pip list | grep -E "pandas|sklearn|matplotlib"`
4. Reinstall all packages: `pip install -r requirements.txt --upgrade`

---

## 🎬 Enjoy Your CinePredict Experience!

Good luck predicting movie success! 🚀

**Dashboard Shortcuts:**
- **Prev/Next buttons**: Navigate between charts
- **Open Folder**: Access raw PNG files
- **Tabs**: Switch between Visualizations, Metrics, and Insights

---

**Version**: 1.0  
**Last Updated**: April 2026  
**Status**: Production Ready ✓

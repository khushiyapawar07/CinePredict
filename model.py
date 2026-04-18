"""
model.py ─ Data Mining: Train, Evaluate & Predict Movie Success
Applies Logistic Regression, Decision Tree, Random Forest
"""

import os
import sys
import sqlite3
import warnings
import numpy as np
import pandas as pd

from sklearn.model_selection   import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing     import StandardScaler
from sklearn.linear_model      import LogisticRegression
from sklearn.tree              import DecisionTreeClassifier
from sklearn.ensemble          import RandomForestClassifier
from sklearn.metrics           import (accuracy_score, precision_score,
                                        recall_score, f1_score,
                                        confusion_matrix, classification_report,
                                        roc_auc_score)
from sklearn.pipeline          import Pipeline

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import DB_PATH, print_section, ensure_output_dir, get_logger

log = get_logger("Model")

# ── Feature columns used for training ─────────────────────────────────────────
FEATURE_COLS = [
    "budget",
    "rating",
    "votes",
    "genre_encoded",
    "director_success_rate",
    "cast_popularity_score",
    "season_encoded",
    "popularity_score",
]
TARGET_COL = "success"


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING FROM WAREHOUSE
# ══════════════════════════════════════════════════════════════════════════════
def load_features() -> pd.DataFrame:
    print_section("LOADING FEATURES FROM WAREHOUSE")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"""
        SELECT
            f.movie_id, f.title,
            f.budget, f.revenue, f.roi, f.rating, f.votes,
            f.genre_encoded, f.director_success_rate,
            f.cast_popularity_score, f.season_encoded,
            f.popularity_score, f.budget_tier, f.success,
            g.genre_name, d.director_name
        FROM fact_movies f
        LEFT JOIN dim_genre    g ON f.genre_id    = g.genre_id
        LEFT JOIN dim_director d ON f.director_id = d.director_id
        """,
        conn,
    )
    conn.close()

    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
    log.info(f"  Dataset shape: {df.shape}")
    log.info(f"  Class distribution:\n{df[TARGET_COL].value_counts().to_string()}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# MODEL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════
def get_models() -> dict:
    return {
        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=500, class_weight="balanced",
                C=1.0, solver="lbfgs", random_state=42
            )),
        ]),
        "Decision Tree": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", DecisionTreeClassifier(
                max_depth=6, min_samples_split=5,
                class_weight="balanced", random_state=42
            )),
        ]),
        "Random Forest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=200, max_depth=8,
                min_samples_split=4, class_weight="balanced",
                random_state=42, n_jobs=-1
            )),
        ]),
    }


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING & EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
def evaluate_model(model, X_test, y_test, model_name: str) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    auc  = roc_auc_score(y_test, y_prob)
    cm   = confusion_matrix(y_test, y_pred)

    print(f"\n{'─'*50}")
    print(f"  {model_name}")
    print(f"{'─'*50}")
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"  ROC-AUC   : {auc:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"            Pred FLOP  Pred HIT")
    print(f"  Act FLOP  {cm[0,0]:>8}  {cm[0,1]:>8}")
    print(f"  Act HIT   {cm[1,0]:>8}  {cm[1,1]:>8}")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred,
                                 target_names=["FLOP", "HIT"], zero_division=0))
    return {
        "model_name": model_name,
        "accuracy":   acc,
        "precision":  prec,
        "recall":     rec,
        "f1_score":   f1,
        "roc_auc":    auc,
        "confusion_matrix": cm,
    }


def train_and_evaluate(df: pd.DataFrame) -> tuple:
    print_section("MODEL TRAINING & EVALUATION")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    # Fill any residual NaNs with column medians
    X = X.fillna(X.median())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    log.info(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    models    = get_models()
    results   = {}
    skf       = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best_name = None
    best_f1   = -1

    for name, pipeline in models.items():
        # Cross-validation
        cv_scores = cross_val_score(pipeline, X_train, y_train,
                                     cv=skf, scoring="f1", n_jobs=-1)
        log.info(f"\n  [{name}] CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        # Fit
        pipeline.fit(X_train, y_train)

        # Evaluate
        res = evaluate_model(pipeline, X_test, y_test, name)
        res["cv_f1_mean"] = cv_scores.mean()
        res["cv_f1_std"]  = cv_scores.std()
        results[name]     = res

        if res["f1_score"] > best_f1:
            best_f1   = res["f1_score"]
            best_name = name

    # Feature importance from Random Forest
    rf_pipeline = models["Random Forest"]
    rf_clf      = rf_pipeline.named_steps["clf"]
    importances = pd.Series(
        rf_clf.feature_importances_, index=FEATURE_COLS
    ).sort_values(ascending=False)

    print_section("FEATURE IMPORTANCES (Random Forest)")
    for feat, imp in importances.items():
        bar = "█" * int(imp * 40)
        print(f"  {feat:<28} {imp:.4f}  {bar}")

    print_section("MODEL COMPARISON SUMMARY")
    summary_rows = []
    for name, res in results.items():
        marker = " ◄ BEST" if name == best_name else ""
        print(f"  {name:<25} Acc={res['accuracy']:.3f}  "
              f"F1={res['f1_score']:.3f}  AUC={res['roc_auc']:.3f}{marker}")
        summary_rows.append({
            "Model":     name,
            "Accuracy":  round(res["accuracy"],  4),
            "Precision": round(res["precision"], 4),
            "Recall":    round(res["recall"],    4),
            "F1-Score":  round(res["f1_score"],  4),
            "ROC-AUC":   round(res["roc_auc"],   4),
            "CV F1":     f"{res['cv_f1_mean']:.4f} ± {res['cv_f1_std']:.4f}",
        })

    summary_df = pd.DataFrame(summary_rows)
    out = ensure_output_dir()
    summary_df.to_csv(os.path.join(out, "model_comparison.csv"), index=False)

    # Return best model pipeline for prediction
    best_pipeline = models[best_name]
    return best_pipeline, results, best_name, importances, (X_train, X_test, y_train, y_test)


# ══════════════════════════════════════════════════════════════════════════════
# PREDICTION
# ══════════════════════════════════════════════════════════════════════════════
def predict_movie(
    model,
    budget:                float,
    rating:                float,
    votes:                 int,
    genre_encoded:         int,
    director_success_rate: float,
    cast_popularity_score: float,
    season_encoded:        int,
    popularity_score:      float,
    title:                 str = "Unknown Movie",
) -> dict:
    """Predict HIT or FLOP for a single movie."""

    X_new = pd.DataFrame([{
        "budget":                budget,
        "rating":                rating,
        "votes":                 votes,
        "genre_encoded":         genre_encoded,
        "director_success_rate": director_success_rate,
        "cast_popularity_score": cast_popularity_score,
        "season_encoded":        season_encoded,
        "popularity_score":      popularity_score,
    }])

    pred       = model.predict(X_new)[0]
    prob_hit   = model.predict_proba(X_new)[0][1]
    label      = "HIT 🎬" if pred == 1 else "FLOP 💸"
    confidence = f"{prob_hit * 100:.1f}%"

    print_section(f"PREDICTION: {title}")
    print(f"  Verdict     : {label}")
    print(f"  Confidence  : {confidence} probability of being a HIT")
    print(f"  Budget      : ${budget:>15,.0f}")
    print(f"  Rating      : {rating}")
    print(f"  Votes       : {votes:,}")
    print(f"  Director SR : {director_success_rate:.2%}")
    print(f"  Cast Popul. : {cast_popularity_score}")

    return {"title": title, "prediction": label, "confidence": confidence, "prob_hit": prob_hit}


# ══════════════════════════════════════════════════════════════════════════════
# DEMO PREDICTIONS ON SAMPLE MOVIES
# ══════════════════════════════════════════════════════════════════════════════
def run_demo_predictions(model) -> None:
    print_section("DEMO PREDICTIONS — NEW MOVIES")

    test_cases = [
        dict(title="Big Budget Action Blockbuster",
             budget=200_000_000, rating=7.8, votes=500_000,
             genre_encoded=0, director_success_rate=0.75,
             cast_popularity_score=92.0, season_encoded=2,
             popularity_score=65.0),
        dict(title="Low Budget Indie Drama",
             budget=3_000_000, rating=7.5, votes=40_000,
             genre_encoded=3, director_success_rate=0.60,
             cast_popularity_score=55.0, season_encoded=3,
             popularity_score=32.0),
        dict(title="Mid Budget Horror",
             budget=15_000_000, rating=6.8, votes=180_000,
             genre_encoded=4, director_success_rate=0.50,
             cast_popularity_score=68.0, season_encoded=3,
             popularity_score=41.0),
        dict(title="Overbudget Sci-Fi Flop",
             budget=250_000_000, rating=5.5, votes=80_000,
             genre_encoded=7, director_success_rate=0.30,
             cast_popularity_score=70.0, season_encoded=1,
             popularity_score=28.0),
    ]

    for case in test_cases:
        predict_movie(model, **case)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def run_models() -> tuple:
    df                    = load_features()
    best_model, results, best_name, importances, splits = train_and_evaluate(df)
    run_demo_predictions(best_model)
    return best_model, results, best_name, importances, df


if __name__ == "__main__":
    run_models()

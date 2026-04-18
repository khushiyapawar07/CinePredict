"""
visualize.py ─ Visualization module
Movie Success Prediction System
Generates 8 production-quality charts saved to outputs/
"""

import os
import sys
import sqlite3
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.gridspec import GridSpec
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import DB_PATH, ensure_output_dir, print_section, get_logger

log = get_logger("Visualize")

# ── Style ──────────────────────────────────────────────────────────────────────
PALETTE  = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261", "#264653"]
HIT_CLR  = "#2A9D8F"
FLOP_CLR = "#E63946"

plt.rcParams.update({
    "figure.facecolor": "#FAFAFA",
    "axes.facecolor":   "#F5F5F5",
    "axes.edgecolor":   "#CCCCCC",
    "axes.grid":        True,
    "grid.color":       "#DDDDDD",
    "grid.linestyle":   "--",
    "grid.linewidth":   0.6,
    "font.family":      "DejaVu Sans",
    "font.size":        11,
})


def _load() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT f.*, g.genre_name, d.director_name,
               t.release_year, t.release_month, t.season
        FROM fact_movies f
        LEFT JOIN dim_genre    g ON f.genre_id    = g.genre_id
        LEFT JOIN dim_director d ON f.director_id = d.director_id
        LEFT JOIN dim_time     t ON f.time_id     = t.time_id
        """,
        conn,
    )
    conn.close()
    df = df.dropna(subset=["budget", "revenue", "rating"])
    df["label"] = df["success"].map({1: "HIT", 0: "FLOP"})
    return df


def _save(fig, name: str) -> str:
    out  = ensure_output_dir()
    path = os.path.join(out, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    log.info(f"  Saved → {path}")
    return path


# ══════════════════════════════════════════════════════════════════════════════
# 1. BUDGET vs REVENUE scatter
# ══════════════════════════════════════════════════════════════════════════════
def plot_budget_vs_revenue(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(10, 7))

    for label, color in [("HIT", HIT_CLR), ("FLOP", FLOP_CLR)]:
        sub = df[df["label"] == label]
        ax.scatter(sub["budget"] / 1e6, sub["revenue"] / 1e6,
                   c=color, alpha=0.70, s=60, label=label, edgecolors="white", linewidths=0.4)

    # Break-even line
    lim = max(df["budget"].max(), df["revenue"].max()) / 1e6
    ax.plot([0, lim], [0, lim], "--", color="#888", lw=1.4, label="Break-even")
    # ROI = 1.5 line
    ax.plot([0, lim], [0, lim * 1.5], ":", color="#E9C46A", lw=1.4, label="ROI = 1.5×")

    ax.set_xlabel("Budget (USD Millions)", fontsize=12)
    ax.set_ylabel("Revenue (USD Millions)", fontsize=12)
    ax.set_title("Budget vs Revenue — HIT / FLOP", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    return _save(fig, "1_budget_vs_revenue.png")


# ══════════════════════════════════════════════════════════════════════════════
# 2. GENRE vs SUCCESS RATE
# ══════════════════════════════════════════════════════════════════════════════
def plot_genre_success(df: pd.DataFrame) -> str:
    genre_stats = (
        df.groupby("genre_name")["success"]
          .agg(total="count", hits="sum")
          .assign(hit_rate=lambda x: x["hits"] / x["total"] * 100)
          .query("total >= 3")
          .sort_values("hit_rate", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = [HIT_CLR if r >= 50 else FLOP_CLR for r in genre_stats["hit_rate"]]
    bars   = ax.barh(genre_stats.index, genre_stats["hit_rate"], color=colors,
                     edgecolor="white", linewidth=0.6)

    for bar, (_, row) in zip(bars, genre_stats.iterrows()):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{row['hit_rate']:.0f}%  (n={row['total']:.0f})",
                va="center", fontsize=9)

    ax.axvline(50, color="#888", lw=1.2, linestyle="--", label="50% threshold")
    ax.set_xlabel("Hit Rate (%)", fontsize=12)
    ax.set_title("Success Rate by Genre", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 115)
    ax.legend()

    return _save(fig, "2_genre_success_rate.png")


# ══════════════════════════════════════════════════════════════════════════════
# 3. ROI DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════════════
def plot_roi_distribution(df: pd.DataFrame) -> str:
    roi = df["roi"].replace([np.inf, -np.inf], np.nan).dropna()
    roi_clipped = roi.clip(-1, 15)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Histogram
    ax = axes[0]
    ax.hist(roi_clipped[df.loc[roi_clipped.index, "success"] == 1],
            bins=30, alpha=0.7, color=HIT_CLR, label="HIT", edgecolor="white")
    ax.hist(roi_clipped[df.loc[roi_clipped.index, "success"] == 0],
            bins=30, alpha=0.7, color=FLOP_CLR, label="FLOP", edgecolor="white")
    ax.axvline(1.5, color="#E9C46A", lw=2, linestyle="--", label="ROI threshold (1.5×)")
    ax.set_xlabel("ROI (Revenue / Budget)", fontsize=12)
    ax.set_ylabel("Number of Movies", fontsize=12)
    ax.set_title("ROI Distribution", fontsize=13, fontweight="bold")
    ax.legend()

    # KDE
    ax2 = axes[1]
    for label, color in [("HIT", HIT_CLR), ("FLOP", FLOP_CLR)]:
        subset = roi_clipped[df.loc[roi_clipped.index, "label"] == label]
        if len(subset) > 2:
            sns.kdeplot(subset, ax=ax2, color=color, fill=True, alpha=0.35, label=label)
    ax2.axvline(1.5, color="#E9C46A", lw=2, linestyle="--", label="Threshold")
    ax2.set_xlabel("ROI", fontsize=12)
    ax2.set_title("ROI Density (KDE)", fontsize=13, fontweight="bold")
    ax2.legend()

    fig.suptitle("Return on Investment Analysis", fontsize=15, fontweight="bold", y=1.01)
    return _save(fig, "3_roi_distribution.png")


# ══════════════════════════════════════════════════════════════════════════════
# 4. MODEL COMPARISON BAR CHART
# ══════════════════════════════════════════════════════════════════════════════
def plot_model_comparison(results: dict) -> str:
    metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    labels  = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    models  = list(results.keys())

    x   = np.arange(len(metrics))
    w   = 0.25
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (mname, color) in enumerate(zip(models, PALETTE)):
        vals = [results[mname][m] for m in metrics]
        bars = ax.bar(x + i * w, vals, w, label=mname, color=color,
                      edgecolor="white", linewidth=0.6)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + w)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Model Performance Comparison", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)

    return _save(fig, "4_model_comparison.png")


# ══════════════════════════════════════════════════════════════════════════════
# 5. CONFUSION MATRICES (3 models side by side)
# ══════════════════════════════════════════════════════════════════════════════
def plot_confusion_matrices(results: dict) -> str:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, (mname, res) in zip(axes, results.items()):
        cm  = res["confusion_matrix"]
        disp = ConfusionMatrixDisplay(cm, display_labels=["FLOP", "HIT"])
        disp.plot(ax=ax, colorbar=False, cmap="Blues")
        ax.set_title(mname, fontsize=12, fontweight="bold")

    fig.suptitle("Confusion Matrices — All Models", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return _save(fig, "5_confusion_matrices.png")


# ══════════════════════════════════════════════════════════════════════════════
# 6. FEATURE IMPORTANCE (Random Forest)
# ══════════════════════════════════════════════════════════════════════════════
def plot_feature_importance(importances: pd.Series) -> str:
    fig, ax = plt.subplots(figsize=(10, 6))
    colors  = [PALETTE[i % len(PALETTE)] for i in range(len(importances))]

    bars = ax.barh(importances.index[::-1], importances.values[::-1],
                   color=colors[::-1], edgecolor="white", linewidth=0.5)
    for bar in bars:
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.3f}", va="center", fontsize=9)

    ax.set_xlabel("Importance Score", fontsize=12)
    ax.set_title("Feature Importances — Random Forest", fontsize=14, fontweight="bold")
    ax.set_xlim(0, importances.max() * 1.25)

    return _save(fig, "6_feature_importance.png")


# ══════════════════════════════════════════════════════════════════════════════
# 7. BUDGET TIER vs HIT RATE
# ══════════════════════════════════════════════════════════════════════════════
def plot_budget_tier_vs_hitrate(df: pd.DataFrame) -> str:
    order = ["Low", "Mid", "High", "Blockbuster"]
    df["budget_tier"] = pd.Categorical(df["budget_tier"], categories=order, ordered=True)

    tier_stats = (
        df.groupby("budget_tier", observed=True)["success"]
          .agg(total="count", hits="sum")
          .assign(hit_rate=lambda x: x["hits"] / x["total"] * 100)
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(tier_stats.index, tier_stats["hit_rate"],
                  color=PALETTE[:4], edgecolor="white", linewidth=0.7, width=0.55)

    for bar, (_, row) in zip(bars, tier_stats.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{row['hit_rate']:.0f}%\n(n={row['total']:.0f})",
                ha="center", va="bottom", fontsize=10)

    ax.axhline(50, color="#888", lw=1.2, linestyle="--", label="50%")
    ax.set_ylim(0, 110)
    ax.set_xlabel("Budget Tier", fontsize=12)
    ax.set_ylabel("Hit Rate (%)", fontsize=12)
    ax.set_title("Hit Rate by Budget Tier", fontsize=14, fontweight="bold")
    ax.legend()

    return _save(fig, "7_budget_tier_hitrate.png")


# ══════════════════════════════════════════════════════════════════════════════
# 8. CORRELATION HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
def plot_correlation_heatmap(df: pd.DataFrame) -> str:
    cols = ["budget", "revenue", "rating", "votes", "roi",
            "cast_popularity_score", "director_success_rate", "popularity_score", "success"]
    corr = df[cols].dropna().corr()

    fig, ax = plt.subplots(figsize=(11, 9))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn",
                vmin=-1, vmax=1, linewidths=0.5, ax=ax,
                annot_kws={"size": 9})
    ax.set_title("Feature Correlation Matrix", fontsize=14, fontweight="bold")
    fig.tight_layout()

    return _save(fig, "8_correlation_heatmap.png")


# ══════════════════════════════════════════════════════════════════════════════
# MASTER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def plot_dashboard(df: pd.DataFrame, results: dict, importances: pd.Series) -> str:
    fig = plt.figure(figsize=(20, 24))
    fig.patch.set_facecolor("#FAFAFA")
    gs = GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.35)

    # ── Panel 1: Budget vs Revenue ────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    for label, color in [("HIT", HIT_CLR), ("FLOP", FLOP_CLR)]:
        sub = df[df["label"] == label]
        ax1.scatter(sub["budget"] / 1e6, sub["revenue"] / 1e6,
                    c=color, alpha=0.65, s=50, label=label,
                    edgecolors="white", linewidths=0.4)
    lim = max(df["budget"].max(), df["revenue"].max()) / 1e6
    ax1.plot([0, lim], [0, lim], "--", color="#888", lw=1.2)
    ax1.plot([0, lim], [0, lim * 1.5], ":", color="#E9C46A", lw=1.2, label="ROI=1.5×")
    ax1.set_xlabel("Budget (M USD)"); ax1.set_ylabel("Revenue (M USD)")
    ax1.set_title("Budget vs Revenue", fontweight="bold")
    ax1.legend(fontsize=9)

    # ── Panel 2: Genre Success Rate ───────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    gs2 = (df.groupby("genre_name")["success"]
             .agg(total="count", hits="sum")
             .assign(hr=lambda x: x["hits"] / x["total"] * 100)
             .query("total >= 3")
             .sort_values("hr"))
    colors2 = [HIT_CLR if r >= 50 else FLOP_CLR for r in gs2["hr"]]
    ax2.barh(gs2.index, gs2["hr"], color=colors2, edgecolor="white")
    ax2.axvline(50, color="#888", lw=1, linestyle="--")
    ax2.set_xlabel("Hit Rate (%)"); ax2.set_title("Genre vs Success Rate", fontweight="bold")

    # ── Panel 3: ROI Distribution ─────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    roi = df["roi"].replace([np.inf, -np.inf], np.nan).dropna().clip(-1, 15)
    ax3.hist(roi[df.loc[roi.index, "success"] == 1], bins=25, alpha=0.7,
             color=HIT_CLR, label="HIT", edgecolor="white")
    ax3.hist(roi[df.loc[roi.index, "success"] == 0], bins=25, alpha=0.7,
             color=FLOP_CLR, label="FLOP", edgecolor="white")
    ax3.axvline(1.5, color="#E9C46A", lw=2, linestyle="--", label="Threshold")
    ax3.set_xlabel("ROI"); ax3.set_title("ROI Distribution", fontweight="bold")
    ax3.legend(fontsize=9)

    # ── Panel 4: Model Comparison ─────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    x = np.arange(len(metrics))
    w = 0.25
    for i, (mname, color) in enumerate(zip(results.keys(), PALETTE)):
        vals = [results[mname][m] for m in metrics]
        ax4.bar(x + i * w, vals, w, label=mname, color=color, edgecolor="white")
    ax4.set_xticks(x + w)
    ax4.set_xticklabels(["Acc", "Prec", "Rec", "F1", "AUC"], fontsize=9)
    ax4.set_ylim(0, 1.12); ax4.set_title("Model Comparison", fontweight="bold")
    ax4.legend(fontsize=8)

    # ── Panel 5: Feature Importance ───────────────────────────────────────────
    ax5 = fig.add_subplot(gs[2, 0])
    colors5 = [PALETTE[i % len(PALETTE)] for i in range(len(importances))]
    ax5.barh(importances.index[::-1], importances.values[::-1],
             color=colors5[::-1], edgecolor="white")
    ax5.set_xlabel("Importance"); ax5.set_title("Feature Importance (RF)", fontweight="bold")

    # ── Panel 6: Budget Tier Hit Rate ─────────────────────────────────────────
    ax6 = fig.add_subplot(gs[2, 1])
    order = ["Low", "Mid", "High", "Blockbuster"]
    df["budget_tier"] = pd.Categorical(df["budget_tier"], categories=order, ordered=True)
    ts = (df.groupby("budget_tier", observed=True)["success"]
            .agg(total="count", hits="sum")
            .assign(hr=lambda x: x["hits"] / x["total"] * 100))
    ax6.bar(ts.index, ts["hr"], color=PALETTE[:4], edgecolor="white", width=0.5)
    ax6.axhline(50, color="#888", lw=1, linestyle="--")
    ax6.set_ylim(0, 110); ax6.set_ylabel("Hit Rate (%)")
    ax6.set_title("Budget Tier vs Hit Rate", fontweight="bold")

    # ── Panel 7: Correlation Heat (lower triangle) ────────────────────────────
    ax7 = fig.add_subplot(gs[3, :])
    cols = ["budget", "revenue", "rating", "votes", "roi",
            "cast_popularity_score", "director_success_rate", "popularity_score", "success"]
    corr = df[cols].dropna().corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn",
                vmin=-1, vmax=1, linewidths=0.4, ax=ax7, annot_kws={"size": 8})
    ax7.set_title("Feature Correlation Matrix", fontweight="bold")

    fig.suptitle("Movie Success Prediction — Analytics Dashboard",
                 fontsize=18, fontweight="bold", y=1.005)

    return _save(fig, "0_dashboard.png")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def run_visualizations(results: dict = None, importances: pd.Series = None) -> list:
    print_section("GENERATING VISUALIZATIONS")

    df = _load()
    paths = []

    paths.append(plot_budget_vs_revenue(df))
    paths.append(plot_genre_success(df))
    paths.append(plot_roi_distribution(df))
    paths.append(plot_budget_tier_vs_hitrate(df))
    paths.append(plot_correlation_heatmap(df))

    if results:
        paths.append(plot_model_comparison(results))
        paths.append(plot_confusion_matrices(results))

    if importances is not None:
        paths.append(plot_feature_importance(importances))

    if results and importances is not None:
        paths.append(plot_dashboard(df, results, importances))

    log.info(f"\n  ✓ {len(paths)} charts saved to outputs/")
    return paths


if __name__ == "__main__":
    run_visualizations()

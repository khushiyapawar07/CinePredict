"""
utils.py - Shared utilities for Movie Success Prediction System
"""

import sqlite3
import os
import logging
import pandas as pd
import numpy as np

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "data", "movie_warehouse.db")
DATA_PATH  = os.path.join(BASE_DIR, "data", "movies_sample.csv")
SQL_PATH   = os.path.join(BASE_DIR, "warehouse.sql")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Success thresholds
ROI_THRESHOLD     = 1.5   # ROI > 1.5 → HIT
REVENUE_THRESHOLD = 0     # revenue > budget → also HIT

# Budget tiers (USD)
BUDGET_TIERS = {
    "Low":         (0,       10_000_000),
    "Mid":         (10_000_001, 50_000_000),
    "High":        (50_000_001, 150_000_000),
    "Blockbuster": (150_000_001, float("inf")),
}

# Cast popularity tiers
CAST_TIERS = {
    "Low":       (0,    65),
    "Medium":    (65,   75),
    "High":      (75,   85),
    "Superstar": (85,   float("inf")),
}

SEASON_MAP = {
    1: "Winter",  2: "Winter", 3: "Spring",
    4: "Spring",  5: "Summer", 6: "Summer",
    7: "Summer",  8: "Summer", 9: "Fall",
    10: "Fall",   11: "Holiday", 12: "Holiday",
}

BLOCKBUSTER_MONTHS = {5, 6, 7, 8, 11, 12}

# ── Logging ────────────────────────────────────────────────────────────────────
def get_logger(name: str = "MoviePrediction") -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)


# ── Database helpers ───────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def run_query(sql: str, params=()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute_sql(sql: str, params=(), conn=None) -> None:
    close = conn is None
    if conn is None:
        conn = get_connection()
    conn.execute(sql, params)
    if close:
        conn.commit()
        conn.close()


# ── Feature helpers ────────────────────────────────────────────────────────────
def classify_budget(budget: float) -> str:
    for tier, (lo, hi) in BUDGET_TIERS.items():
        if lo <= budget <= hi:
            return tier
    return "Low"


def classify_cast(popularity: float) -> str:
    for tier, (lo, hi) in CAST_TIERS.items():
        if lo <= popularity < hi:
            return tier
    return "Low"


def compute_roi(revenue: float, budget: float) -> float:
    """ROI = revenue / budget; returns NaN if budget == 0."""
    if budget == 0:
        return float("nan")
    return round(revenue / budget, 4)


def is_success(revenue: float, budget: float) -> int:
    """
    Success label:
        1 (HIT)  if ROI > ROI_THRESHOLD OR revenue > budget
        0 (FLOP) otherwise
    """
    if budget == 0:
        return 0
    roi = revenue / budget
    return int(roi > ROI_THRESHOLD or revenue > budget)


def compute_popularity_score(votes: int, rating: float, roi: float) -> float:
    """
    Composite popularity score (0-100):
        40% normalised votes + 40% rating/10 + 20% ROI contribution
    """
    vote_score   = min(votes / 1_000_000, 1.0) * 40
    rating_score = (rating / 10.0) * 40
    roi_capped   = min(max(roi if not np.isnan(roi) else 0, 0), 10)
    roi_score    = (roi_capped / 10.0) * 20
    return round(vote_score + rating_score + roi_score, 2)


def get_decade(year: int) -> str:
    decade = (year // 10) * 10
    return f"{decade}s"


# ── Reporting helpers ──────────────────────────────────────────────────────────
def print_section(title: str, width: int = 60) -> None:
    print("\n" + "═" * width)
    print(f"  {title}")
    print("═" * width)


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR

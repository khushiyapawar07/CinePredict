"""
etl.py ─ Extract → Transform → Load pipeline
Movie Success Prediction System
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    get_logger, get_connection, DB_PATH, DATA_PATH, SQL_PATH,
    classify_budget, classify_cast, compute_roi, is_success,
    compute_popularity_score, get_decade, SEASON_MAP, BLOCKBUSTER_MONTHS,
    print_section, ensure_output_dir,
)

log = get_logger("ETL")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 ─ EXTRACT
# ══════════════════════════════════════════════════════════════════════════════
def extract(filepath: str = DATA_PATH) -> pd.DataFrame:
    print_section("STEP 1 · EXTRACT")
    log.info(f"Loading raw data from: {filepath}")
    df = pd.read_csv(filepath)
    log.info(f"  Raw shape: {df.shape}")
    log.info(f"  Columns  : {list(df.columns)}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 ─ TRANSFORM
# ══════════════════════════════════════════════════════════════════════════════
def transform(df: pd.DataFrame) -> dict:
    """
    Returns a dict of clean DataFrames ready for loading into the warehouse:
      {
        'dim_genre':    ...,
        'dim_director': ...,
        'dim_cast':     ...,
        'dim_time':     ...,
        'fact_movies':  ...,
      }
    """
    print_section("STEP 2 · TRANSFORM")

    # ── 2.1  De-duplicate ────────────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates(subset=["movie_id"]).copy()
    log.info(f"  De-duplication: {before} → {len(df)} rows")

    # ── 2.2  Handle missing values ───────────────────────────────────────────
    log.info("  Handling missing values …")
    df["budget"]          = pd.to_numeric(df["budget"],          errors="coerce").fillna(0)
    df["revenue"]         = pd.to_numeric(df["revenue"],         errors="coerce").fillna(0)
    df["rating"]          = pd.to_numeric(df["rating"],          errors="coerce")
    df["votes"]           = pd.to_numeric(df["votes"],           errors="coerce").fillna(0).astype(int)
    df["cast_popularity"] = pd.to_numeric(df["cast_popularity"], errors="coerce")
    df["release_year"]    = pd.to_numeric(df["release_year"],    errors="coerce")
    df["release_month"]   = pd.to_numeric(df["release_month"],   errors="coerce")

    df["rating"].fillna(df["rating"].median(), inplace=True)
    df["cast_popularity"].fillna(df["cast_popularity"].median(), inplace=True)
    df["release_year"].fillna(df["release_year"].mode()[0],  inplace=True)
    df["release_month"].fillna(6, inplace=True)  # default → June
    df["genre"].fillna("Unknown", inplace=True)
    df["director"].fillna("Unknown", inplace=True)

    df = df.astype({
        "release_year":  int,
        "release_month": int,
    })

    missing_after = df.isnull().sum().sum()
    log.info(f"  Missing values remaining: {missing_after}")

    # ── 2.3  Feature Engineering ─────────────────────────────────────────────
    log.info("  Computing derived features …")

    df["roi"]    = df.apply(lambda r: compute_roi(r["revenue"], r["budget"]), axis=1)
    df["profit"] = df["revenue"] - df["budget"]
    df["success"] = df.apply(lambda r: is_success(r["revenue"], r["budget"]), axis=1)

    df["season"]   = df["release_month"].map(SEASON_MAP)
    df["is_blockbuster_season"] = df["release_month"].apply(
        lambda m: 1 if m in BLOCKBUSTER_MONTHS else 0
    )
    df["decade"] = df["release_year"].apply(get_decade)
    df["budget_tier"] = df["budget"].apply(classify_budget)
    df["star_power_tier"] = df["cast_popularity"].apply(classify_cast)

    df["popularity_score"] = df.apply(
        lambda r: compute_popularity_score(
            r["votes"], r["rating"],
            r["roi"] if not pd.isna(r["roi"]) else 0
        ),
        axis=1,
    )

    # ── 2.4  Director success rate (global, computed from the dataset) ────────
    dir_stats = (
        df.groupby("director")["success"]
          .agg(total="count", hits="sum")
          .assign(success_rate=lambda x: (x["hits"] / x["total"]).round(4))
          .reset_index()
    )
    df = df.merge(dir_stats[["director", "success_rate"]]
                  .rename(columns={"success_rate": "director_success_rate"}),
                  on="director", how="left")

    # ── 2.5  Encode categorical variables ────────────────────────────────────
    log.info("  Encoding categorical variables …")
    genre_cats = {g: i for i, g in enumerate(sorted(df["genre"].unique()))}
    df["genre_encoded"] = df["genre"].map(genre_cats)

    season_cats = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3, "Holiday": 4}
    df["season_encoded"] = df["season"].map(season_cats).fillna(0).astype(int)

    # ── 2.6  Build dimension tables ──────────────────────────────────────────
    log.info("  Building dimension tables …")

    # dim_genre
    dim_genre = (
        df[["genre"]].drop_duplicates()
          .rename(columns={"genre": "genre_name"})
          .assign(genre_category=lambda x: x["genre_name"].map({
              "Action": "Blockbuster", "Animation": "Blockbuster",
              "Sci-Fi": "Blockbuster", "Adventure": "Blockbuster",
              "Horror": "Indie",       "Thriller": "Indie",
              "Drama": "Prestige",     "Comedy": "Prestige",
              "Biography": "Prestige", "Crime": "Prestige",
              "Musical": "Prestige",   "Mystery": "Prestige",
              "Romance": "Prestige",   "War": "Prestige",
              "Western": "Prestige",   "Fantasy": "Blockbuster",
              "Documentary": "Indie",
          }).fillna("Other"))
          .reset_index(drop=True)
    )
    dim_genre.index = dim_genre.index + 1
    dim_genre.index.name = "genre_id"
    dim_genre = dim_genre.reset_index()

    # dim_director
    dir_agg = (
        df.groupby("director").agg(
            total_movies  = ("movie_id", "count"),
            avg_rating    = ("rating",   "mean"),
            success_rate  = ("success",  "mean"),
            career_total_revenue = ("revenue", "sum"),
        ).round(4).reset_index()
          .rename(columns={"director": "director_name"})
    )
    dir_agg.index = dir_agg.index + 1
    dir_agg.index.name = "director_id"
    dim_director = dir_agg.reset_index()

    # dim_cast
    dim_cast = (
        df[["movie_id", "cast_popularity", "star_power_tier"]]
          .drop_duplicates(subset=["movie_id"])
          .copy()
    )
    dim_cast.index = dim_cast.index + 1
    dim_cast.index.name = "cast_id"
    dim_cast = dim_cast.reset_index()

    # dim_time
    time_df = (
        df[["release_year", "release_month"]].drop_duplicates()
          .assign(
              release_quarter=lambda x: ((x["release_month"] - 1) // 3 + 1),
              season=lambda x: x["release_month"].map(SEASON_MAP),
              is_blockbuster_season=lambda x: x["release_month"].apply(
                  lambda m: 1 if m in BLOCKBUSTER_MONTHS else 0),
              decade=lambda x: x["release_year"].apply(get_decade),
          )
    )
    time_df.index = time_df.index + 1
    time_df.index.name = "time_id"
    dim_time = time_df.reset_index()

    # ── 2.7  Build fact table ────────────────────────────────────────────────
    log.info("  Building fact table …")

    # Merge FK lookups
    df2 = df.merge(dim_genre[["genre_id", "genre_name"]].rename(columns={"genre_name": "genre"}),
                   on="genre", how="left")
    df2 = df2.merge(dim_director[["director_id", "director_name"]].rename(columns={"director_name": "director"}),
                    on="director", how="left")
    df2 = df2.merge(dim_cast[["cast_id", "movie_id"]], on="movie_id", how="left")
    df2 = df2.merge(dim_time[["time_id", "release_year", "release_month"]],
                    on=["release_year", "release_month"], how="left")

    fact_movies = df2[[
        "movie_id", "title",
        "genre_id", "director_id", "cast_id", "time_id",
        "budget", "revenue", "rating", "votes",
        "roi", "profit", "popularity_score", "budget_tier",
        "genre_encoded", "director_success_rate",
        "cast_popularity", "season_encoded", "success",
    ]].rename(columns={"cast_popularity": "cast_popularity_score"})

    hit_rate = df["success"].mean() * 100
    log.info(f"  Success (HIT) rate in dataset: {hit_rate:.1f}%")
    log.info(f"  Fact rows: {len(fact_movies)}")

    return {
        "dim_genre":    dim_genre,
        "dim_director": dim_director,
        "dim_cast":     dim_cast,
        "dim_time":     dim_time,
        "fact_movies":  fact_movies,
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 ─ LOAD
# ══════════════════════════════════════════════════════════════════════════════
def load(tables: dict) -> None:
    print_section("STEP 3 · LOAD")

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Initialise schema
    with open(SQL_PATH) as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema_sql)
    conn.commit()
    log.info(f"  Schema initialised → {DB_PATH}")

    # Load each table
    load_order = ["dim_genre", "dim_director", "dim_cast", "dim_time", "fact_movies"]
    for tbl in load_order:
        df_tbl = tables[tbl]
        df_tbl.to_sql(tbl, conn, if_exists="replace", index=False)
        log.info(f"  Loaded {tbl:20s} → {len(df_tbl):>4} rows")

    conn.commit()
    conn.close()
    log.info("  ✓ All tables loaded successfully")


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
def validate() -> None:
    print_section("VALIDATION")
    conn = sqlite3.connect(DB_PATH)
    for view in ["vw_genre_summary", "vw_director_leaderboard", "vw_yearly_trend"]:
        df = pd.read_sql_query(f"SELECT * FROM {view} LIMIT 5", conn)
        log.info(f"\n  {view}:\n{df.to_string(index=False)}")
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def run_etl(filepath: str = DATA_PATH) -> dict:
    print("\n" + "█" * 60)
    print("  MOVIE SUCCESS PREDICTION — ETL PIPELINE")
    print("█" * 60)

    raw    = extract(filepath)
    tables = transform(raw)
    load(tables)
    validate()

    log.info("\n✓ ETL Pipeline completed successfully!\n")
    return tables


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else DATA_PATH
    run_etl(src)

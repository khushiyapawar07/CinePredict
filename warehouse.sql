-- ============================================================
-- Movie Success Prediction System
-- Data Warehouse Schema (Star Schema Design)
-- SQLite-compatible SQL
-- ============================================================

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- Dimension: Genre
CREATE TABLE IF NOT EXISTS dim_genre (
    genre_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name TEXT NOT NULL UNIQUE,
    genre_category TEXT  -- 'Blockbuster', 'Indie', 'Prestige', etc.
);

-- Dimension: Director
CREATE TABLE IF NOT EXISTS dim_director (
    director_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    director_name        TEXT NOT NULL UNIQUE,
    total_movies         INTEGER DEFAULT 0,
    avg_rating           REAL DEFAULT 0.0,
    success_rate         REAL DEFAULT 0.0,  -- % of movies that were HITs
    career_total_revenue REAL DEFAULT 0.0
);

-- Dimension: Cast (aggregated popularity per movie)
CREATE TABLE IF NOT EXISTS dim_cast (
    cast_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id         INTEGER NOT NULL,
    cast_popularity  REAL DEFAULT 0.0,   -- aggregated popularity score
    star_power_tier  TEXT DEFAULT 'Low', -- 'Low', 'Medium', 'High', 'Superstar'
    UNIQUE(movie_id)
);

-- Dimension: Time
CREATE TABLE IF NOT EXISTS dim_time (
    time_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    release_year  INTEGER NOT NULL,
    release_month INTEGER NOT NULL,
    release_quarter INTEGER,
    season        TEXT,   -- 'Summer', 'Holiday', 'Spring', 'Fall'
    is_blockbuster_season INTEGER DEFAULT 0,  -- 1 if May-Aug or Nov-Dec
    decade        TEXT,   -- '1990s', '2000s', etc.
    UNIQUE(release_year, release_month)
);

-- ============================================================
-- FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_movies (
    fact_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id    INTEGER NOT NULL UNIQUE,
    title       TEXT NOT NULL,

    -- Foreign Keys to Dimensions
    genre_id    INTEGER REFERENCES dim_genre(genre_id),
    director_id INTEGER REFERENCES dim_director(director_id),
    cast_id     INTEGER REFERENCES dim_cast(cast_id),
    time_id     INTEGER REFERENCES dim_time(time_id),

    -- Core Metrics (Measures)
    budget      REAL NOT NULL DEFAULT 0,
    revenue     REAL NOT NULL DEFAULT 0,
    rating      REAL DEFAULT 0.0,
    votes       INTEGER DEFAULT 0,

    -- Derived Metrics
    roi              REAL,   -- revenue / budget  (NULL if budget=0)
    profit           REAL,   -- revenue - budget
    popularity_score REAL,   -- engineered feature
    budget_tier      TEXT,   -- 'Low', 'Mid', 'High', 'Blockbuster'

    -- Encoded Features
    genre_encoded    INTEGER DEFAULT 0,
    director_success_rate REAL DEFAULT 0.0,
    cast_popularity_score REAL DEFAULT 0.0,
    season_encoded   INTEGER DEFAULT 0,

    -- Target Variable
    success          INTEGER DEFAULT 0   -- 1 = HIT, 0 = FLOP
);

-- ============================================================
-- INDEXES for query performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_genre     ON fact_movies(genre_id);
CREATE INDEX IF NOT EXISTS idx_fact_director  ON fact_movies(director_id);
CREATE INDEX IF NOT EXISTS idx_fact_time      ON fact_movies(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_success   ON fact_movies(success);
CREATE INDEX IF NOT EXISTS idx_fact_roi       ON fact_movies(roi);

-- ============================================================
-- ANALYTICAL VIEWS
-- ============================================================

-- View: Full star-schema joined table for analysis
CREATE VIEW IF NOT EXISTS vw_movie_analysis AS
SELECT
    f.movie_id,
    f.title,
    g.genre_name,
    d.director_name,
    d.success_rate AS director_success_rate,
    c.cast_popularity,
    c.star_power_tier,
    t.release_year,
    t.release_month,
    t.season,
    t.is_blockbuster_season,
    f.budget,
    f.revenue,
    f.roi,
    f.profit,
    f.rating,
    f.votes,
    f.popularity_score,
    f.budget_tier,
    CASE WHEN f.success = 1 THEN 'HIT' ELSE 'FLOP' END AS prediction_label
FROM fact_movies f
LEFT JOIN dim_genre    g ON f.genre_id    = g.genre_id
LEFT JOIN dim_director d ON f.director_id = d.director_id
LEFT JOIN dim_cast     c ON f.cast_id     = c.cast_id
LEFT JOIN dim_time     t ON f.time_id     = t.time_id;

-- View: Genre performance summary
CREATE VIEW IF NOT EXISTS vw_genre_summary AS
SELECT
    g.genre_name,
    COUNT(f.movie_id)                          AS total_movies,
    SUM(f.success)                            AS hits,
    ROUND(AVG(f.success) * 100, 2)            AS hit_rate_pct,
    ROUND(AVG(f.roi), 3)                      AS avg_roi,
    ROUND(AVG(f.rating), 2)                   AS avg_rating,
    ROUND(SUM(f.revenue) / 1e6, 2)            AS total_revenue_M,
    ROUND(AVG(f.budget) / 1e6, 2)             AS avg_budget_M
FROM fact_movies f
JOIN dim_genre g ON f.genre_id = g.genre_id
GROUP BY g.genre_name
ORDER BY hit_rate_pct DESC;

-- View: Director leaderboard
CREATE VIEW IF NOT EXISTS vw_director_leaderboard AS
SELECT
    d.director_name,
    COUNT(f.movie_id)                          AS total_movies,
    SUM(f.success)                            AS hits,
    ROUND(AVG(f.success) * 100, 2)            AS hit_rate_pct,
    ROUND(AVG(f.roi), 3)                      AS avg_roi,
    ROUND(AVG(f.rating), 2)                   AS avg_rating,
    ROUND(SUM(f.revenue) / 1e6, 2)            AS total_revenue_M
FROM fact_movies f
JOIN dim_director d ON f.director_id = d.director_id
GROUP BY d.director_name
ORDER BY hit_rate_pct DESC, total_movies DESC;

-- View: Year-wise trend
CREATE VIEW IF NOT EXISTS vw_yearly_trend AS
SELECT
    t.release_year,
    COUNT(f.movie_id)                          AS total_movies,
    SUM(f.success)                            AS hits,
    ROUND(AVG(f.success) * 100, 2)            AS hit_rate_pct,
    ROUND(AVG(f.roi), 3)                      AS avg_roi,
    ROUND(SUM(f.revenue) / 1e6, 2)            AS total_revenue_M
FROM fact_movies f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY t.release_year
ORDER BY t.release_year;

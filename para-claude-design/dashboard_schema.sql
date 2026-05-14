-- dashboard.db schema
-- Hermes Dashboard — SQLite database for Streamlit frontend
-- Collector populates this from Hermes state.db + OpenRouter API

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    source          TEXT NOT NULL,          -- 'telegram', 'cli'
    model           TEXT,                   -- 'deepseek/deepseek-v4-pro'
    parent_session_id TEXT,
    started_at      REAL NOT NULL,          -- unix timestamp
    ended_at        REAL,                   -- NULL if active
    end_reason      TEXT,
    message_count   INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    api_call_count  INTEGER DEFAULT 0,
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    cache_read_tokens  INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens   INTEGER DEFAULT 0,
    estimated_cost_usd REAL,
    cost_status     TEXT,                   -- 'estimated', 'unknown'
    billing_provider TEXT,
    title           TEXT,
    -- computed fields
    date            TEXT GENERATED ALWAYS AS (date(started_at, 'unixepoch')) STORED,
    hour            INTEGER GENERATED ALWAYS AS (CAST(strftime('%H', started_at, 'unixepoch') AS INTEGER)) STORED,
    total_tokens    INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens + reasoning_tokens) STORED,
    duration_seconds REAL GENERATED ALWAYS AS (
        CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at ELSE NULL END
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
CREATE INDEX IF NOT EXISTS idx_sessions_model ON sessions(model);
CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);

-- Daily aggregated stats
CREATE TABLE IF NOT EXISTS daily_stats (
    date            TEXT PRIMARY KEY,
    session_count   INTEGER DEFAULT 0,
    message_count   INTEGER DEFAULT 0,
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    cache_read_tokens  INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens   INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    estimated_cost_usd REAL DEFAULT 0.0,
    models_used     TEXT,                   -- JSON array of models
    sources_used    TEXT                    -- JSON array of sources
);

-- Per-model aggregated stats
CREATE TABLE IF NOT EXISTS model_stats (
    model           TEXT PRIMARY KEY,
    session_count   INTEGER DEFAULT 0,
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    cache_read_tokens  INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens   INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    estimated_cost_usd REAL DEFAULT 0.0,
    last_used       REAL                    -- unix timestamp
);

-- OpenRouter account balance snapshots
CREATE TABLE IF NOT EXISTS account_snapshots (
    timestamp       REAL PRIMARY KEY,       -- unix timestamp
    total_credits   REAL,                   -- purchased
    total_usage     REAL,                   -- used
    remaining       REAL GENERATED ALWAYS AS (total_credits - total_usage) STORED
);

-- Collector run log
CREATE TABLE IF NOT EXISTS collector_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      REAL NOT NULL,
    ended_at        REAL,
    status          TEXT DEFAULT 'running', -- 'running', 'success', 'error'
    sessions_added  INTEGER DEFAULT 0,
    sessions_updated INTEGER DEFAULT 0,
    credits_fetched INTEGER DEFAULT 0,      -- 0 or 1
    error_message   TEXT
);

-- Views for convenience
CREATE VIEW IF NOT EXISTS v_daily_costs AS
SELECT date, estimated_cost_usd, session_count, total_tokens
FROM daily_stats ORDER BY date DESC;

CREATE VIEW IF NOT EXISTS v_model_ranking AS
SELECT model, session_count, estimated_cost_usd, total_tokens,
       ROUND(estimated_cost_usd / NULLIF(total_tokens, 0) * 1000000, 4) AS cost_per_1m_tokens
FROM model_stats
WHERE total_tokens > 0
ORDER BY estimated_cost_usd DESC;

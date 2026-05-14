-- Add to dashboard_schema.sql (run after existing schema)
-- High water mark for incremental collection
CREATE TABLE IF NOT EXISTS high_water_mark (
    key         TEXT PRIMARY KEY,
    value       REAL NOT NULL,          -- unix timestamp
    updated_at  REAL NOT NULL
);

-- Initialize if not exists
INSERT OR IGNORE INTO high_water_mark (key, value, updated_at)
VALUES ('last_session_started_at', 0, 0);

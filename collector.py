#!/usr/bin/env python3

"""

Hermes Dashboard Collector v2

==============================

Incremental collector: reads Hermes state.db and OpenRouter API

to build the Hermes Analytics dashboard database (dashboard.db).

Usage:

    python collector.py              # Incremental: new sessions + credits

    python collector.py --full-refresh       # Full rebuild of aggregations

    python collector.py --sessions-only     # Only sessions

    python collector.py --credits-only      # Only OpenRouter balance

    python collector.py --tools-only        # Only tool usage & errors

Designed to run as a cron job. Incremental by default — only processes

sessions newer than the last successful run.

"""

import argparse

import json

import os

import shutil

import sqlite3

import sys

import time

import traceback

from pathlib import Path

import requests

# ── Paths ──────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).resolve().parent

CONFIG_PATH = PROJECT_DIR / "config.yaml"

DB_PATH = PROJECT_DIR / "dashboard.db"

SCHEMA_PATH = PROJECT_DIR / "dashboard_schema.sql"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Session fields to copy

SESSION_FIELDS = [

    "id", "source", "model", "parent_session_id",

    "started_at", "ended_at", "end_reason",

    "message_count", "tool_call_count", "api_call_count",

    "input_tokens", "output_tokens",

    "cache_read_tokens", "cache_write_tokens", "reasoning_tokens",

    "estimated_cost_usd", "cost_status", "billing_provider", "title"

]

# ── Path resolution ────────────────────────────────────────────────

def _norm_path(p):

    p = Path(p)

    if p.exists():

        return p

    if hasattr(p, 'drive') and p.drive:

        wsl = Path("/mnt") / p.drive[0].lower() / p.relative_to(p.anchor)

        if wsl.exists():

            return wsl

    parts = p.parts

    if len(parts) >= 3 and parts[0] == '/' and parts[1] == 'mnt':

        win = Path(parts[2].upper() + ':\\' + '\\'.join(parts[3:]))

        if win.exists():

            return win

    return p

def _find_hermes_dir(config_dir=None):

    candidates = []

    if config_dir:

        candidates.append(Path(config_dir))

    localappdata = os.environ.get("LOCALAPPDATA", "")

    if localappdata:

        candidates.append(Path(localappdata) / "hermes")

    home = Path.home()

    candidates.append(home / "AppData" / "Local" / "hermes")

    for c in candidates[:]:

        p = str(c)

        if len(p) > 1 and p[1:2] == ':':

            drive = p[0].lower()

            rest = p[3:].replace('\\', '/')

            candidates.append(Path(f"/mnt/{drive}/{rest}"))

    for c in candidates:

        resolved = _norm_path(c)

        if resolved.exists():

            return resolved

    return None

HERMES_DIR = _find_hermes_dir()

STATE_DB = HERMES_DIR / "state.db" if HERMES_DIR else None

AUTH_JSON = HERMES_DIR / "auth.json" if HERMES_DIR else None

# ── Config ─────────────────────────────────────────────────────────

def load_config():

    if CONFIG_PATH.exists():

        import yaml

        with open(CONFIG_PATH) as f:

            return yaml.safe_load(f)

    return {}

def get_api_key():

    if not AUTH_JSON or not AUTH_JSON.exists():

        return None

    with open(AUTH_JSON) as f:

        auth = json.load(f)

    pool = auth.get("credential_pool", {}).get("openrouter", [])

    if pool:

        return pool[0].get("access_token")

    return None

# ── Database ───────────────────────────────────────────────────────

def get_management_key():
    """Lee OPENROUTER_MANAGEMENT_KEY del .env via os.getenv"""
    api_key = os.getenv("OPENROUTER_MANAGEMENT_KEY")
    if api_key:
        return api_key
    print("[get_management_key] OPENROUTER_MANAGEMENT_KEY not found in environment")
    return None

    """Read OpenRouter management key from .env file (used for /api/v1/activity endpoint)."""

    env_path = PROJECT_DIR / ".env"

    if not env_path.exists():

        print("[get_management_key] No .env file found at " + str(env_path))

        return None

    try:

        with open(env_path) as f:

            for line in f:

                line = line.strip()

                if line.startswith("OPENROUTER_MANAGEMENT_KEY="):

                    val = line.split("=", 1)[1].strip().strip(chr(34)).strip(chr(39))

                    if val:

                        return val

                    else:

                        print("[get_management_key] OPENROUTER_MANAGEMENT_KEY is empty in .env")

                        return None

        print("[get_management_key] OPENROUTER_MANAGEMENT_KEY not found in .env")

        return None

    except Exception as e:

        print(f"[get_management_key] Error reading .env: {e}")

        return None



def init_db(conn):

    """Apply base schema + v2 additions."""

    schema = SCHEMA_PATH.read_text()

    conn.executescript(schema)

    # v2: high_water_mark table

    conn.executescript("""

        CREATE TABLE IF NOT EXISTS high_water_mark (

            key         TEXT PRIMARY KEY,

            value       REAL NOT NULL,

            updated_at  REAL NOT NULL

        );

        INSERT OR IGNORE INTO high_water_mark (key, value, updated_at)

        VALUES ('last_session_started_at', 0, 0);

    """)

    conn.commit()



def migrate_db(conn):

    """Apply incremental schema migrations."""

    cursor = conn.cursor()

    # Migration 1: Add columns to sessions table for real cost calculation

    try:

        cursor.execute("ALTER TABLE sessions ADD COLUMN actual_cost_calculated REAL")

        print("[migrate_db] Added actual_cost_calculated column to sessions")

    except sqlite3.OperationalError as e:

        if "duplicate column name" not in str(e):

            raise

    try:

        cursor.execute("ALTER TABLE sessions ADD COLUMN price_source TEXT")

        print("[migrate_db] Added price_source column to sessions")

    except sqlite3.OperationalError as e:

        if "duplicate column name" not in str(e):

            raise

    try:

        cursor.execute("ALTER TABLE sessions ADD COLUMN cost_discrepancy REAL")

        print("[migrate_db] Added cost_discrepancy column to sessions")

    except sqlite3.OperationalError as e:

        if "duplicate column name" not in str(e):

            raise

    # Migration 2: Create model_prices table

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS model_prices (

            model_id        TEXT PRIMARY KEY,

            input_price     REAL,

            output_price    REAL,

            cache_read_price REAL,

            cache_write_price REAL,

            reasoning_price REAL,

            timestamp       REAL NOT NULL,

            source          TEXT NOT NULL

        )

    """)

    # Migration 3: Create tool_usage table

    cursor.execute(

        "CREATE TABLE IF NOT EXISTS tool_usage ("

        "id INTEGER PRIMARY KEY AUTOINCREMENT, "

        "session_id TEXT NOT NULL, tool_name TEXT NOT NULL, "

        "timestamp REAL NOT NULL, success BOOLEAN DEFAULT 1, "

        "error_message TEXT, duration_ms REAL, "

        "arguments TEXT, result_summary TEXT)"

    )

    # Migration 4: Create errors_log table

    cursor.execute(

        "CREATE TABLE IF NOT EXISTS errors_log ("

        "id INTEGER PRIMARY KEY AUTOINCREMENT, "

        "timestamp REAL NOT NULL, source TEXT, "

        "error_type TEXT, message TEXT, session_id TEXT, "

        "tool_name TEXT, stack_trace TEXT, "

        "resolved BOOLEAN DEFAULT 0)"

    )

    # Migration 5: Create model_performance table

    cursor.execute(

        "CREATE TABLE IF NOT EXISTS model_performance ("

        "id INTEGER PRIMARY KEY AUTOINCREMENT, "

        "model TEXT NOT NULL, day TEXT, "

        "avg_response_ms REAL, success_rate REAL DEFAULT 1.0, "

        "error_count INTEGER DEFAULT 0, "

        "token_throughput REAL, session_count INTEGER DEFAULT 0)"

    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON tool_usage(session_id)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_usage_tool ON tool_usage(tool_name)")

    conn.commit()

    print("[migrate_db] Schema migrations applied (performance tables ready)")

def fetch_model_prices(conn, api_key=None):

    """

    Fetch current model prices from OpenRouter API and store in model_prices table.

    Returns number of prices fetched or 0 on error.

    """

    if not api_key:

        print("[fetch_model_prices] No API key provided, skipping")

        return 0

    OPENROUTER_BASE = "https://openrouter.ai/api/v1"

    headers = {

        "Authorization": f"Bearer {api_key}",

        "User-Agent": "Hermes-Dashboard/1.0"

    }

    try:

        print("[fetch_model_prices] Fetching model prices from OpenRouter...")

        response = requests.get(f"{OPENROUTER_BASE}/models", headers=headers, timeout=30)

        response.raise_for_status()

        data = response.json()

        if "data" not in data:

            print("[fetch_model_prices] No 'data' field in response")

            return 0

        models = data["data"]

        print(f"[fetch_model_prices] Found {len(models)} models")

        cursor = conn.cursor()

        timestamp = time.time()

        inserted = 0

        for model in models:

            model_id = model.get("id")

            if not model_id:

                continue

            pricing = model.get("pricing", {})

            if not pricing:

                # Some models have no pricing (e.g., free models)

                continue

            # Extract prices - OpenRouter uses keys like "prompt", "completion", etc.

            # Map to our schema

            input_price = pricing.get("prompt")

            output_price = pricing.get("completion") 

            cache_read_price = pricing.get("input_cache_read")

            cache_write_price = pricing.get("input_cache_write")

            reasoning_price = pricing.get("internal_reasoning")

            # Skip if no pricing information at all

            if all(price is None for price in [input_price, output_price, cache_read_price, cache_write_price, reasoning_price]):

                continue

            # Convert to float if string

            def to_float(val):

                if val is None:

                    return None

                try:

                    return float(val)

                except (ValueError, TypeError):

                    return None

            input_price = to_float(input_price)

            output_price = to_float(output_price)

            cache_read_price = to_float(cache_read_price)

            cache_write_price = to_float(cache_write_price)

            reasoning_price = to_float(reasoning_price)

            # Insert or replace

            cursor.execute("""

                INSERT OR REPLACE INTO model_prices 

                (model_id, input_price, output_price, cache_read_price, cache_write_price, reasoning_price, timestamp, source)

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            """, (model_id, input_price, output_price, cache_read_price, cache_write_price, reasoning_price, timestamp, "openrouter_api_v1_models"))

            inserted += 1

        conn.commit()

        print(f"[fetch_model_prices] Inserted/updated {inserted} model prices")

        return inserted

    except requests.exceptions.RequestException as e:

        print(f"[fetch_model_prices] Request error: {e}")

        return 0

    except Exception as e:

        print(f"[fetch_model_prices] Unexpected error: {type(e).__name__}: {e}")

        return 0

def collect_sessions_incremental(conn):

    """Fetch only sessions newer than watermark. Fast incremental path."""

    tmp_db = safe_copy_state_db()

    if not tmp_db:

        return 0, 0

    watermark = get_watermark(conn)

    conn_src = sqlite3.connect(str(tmp_db))

    conn_src.row_factory = sqlite3.Row

    fields_str = ", ".join(SESSION_FIELDS)

    rows = conn_src.execute(

        f"SELECT {fields_str} FROM sessions WHERE started_at > ? ORDER BY started_at",

        (watermark,)

    ).fetchall()

    max_ts = watermark

    added = 0

    updated = 0

    for row in rows:

        d = dict(row)

        max_ts = max(max_ts, d["started_at"])

        values = [d[f] for f in SESSION_FIELDS]

        existing = conn.execute("SELECT id FROM sessions WHERE id = ?", (d["id"],)).fetchone()

        if existing:

            set_clause = ", ".join(f"{f} = ?" for f in SESSION_FIELDS)

            conn.execute(

                f"UPDATE sessions SET {set_clause} WHERE id = ?",

                values + [d["id"]]

            )

            updated += 1

        else:

            placeholders = ", ".join("?" * len(SESSION_FIELDS))

            conn.execute(

                f"INSERT INTO sessions ({fields_str}) VALUES ({placeholders})",

                values

            )

            added += 1

    conn_src.close()

    tmp_db.unlink()

    if added > 0 or updated > 0:

        recompute_aggregates_incremental(conn)

        set_watermark(conn, max_ts)

    return added, updated

def collect_sessions_full(conn):

    """Full refresh: re-read everything, rebuild aggregates."""

    tmp_db = safe_copy_state_db()

    if not tmp_db:

        return 0, 0

    conn_src = sqlite3.connect(str(tmp_db))

    conn_src.row_factory = sqlite3.Row

    fields_str = ", ".join(SESSION_FIELDS)

    rows = conn_src.execute(

        f"SELECT {fields_str} FROM sessions ORDER BY started_at"

    ).fetchall()

    added = 0

    updated = 0

    max_ts = 0

    for row in rows:

        d = dict(row)

        max_ts = max(max_ts, d["started_at"])

        values = [d[f] for f in SESSION_FIELDS]

        existing = conn.execute("SELECT id FROM sessions WHERE id = ?", (d["id"],)).fetchone()

        placeholders = ", ".join("?" * len(SESSION_FIELDS))

        if existing:

            set_clause = ", ".join(f"{f} = ?" for f in SESSION_FIELDS)

            conn.execute(

                f"UPDATE sessions SET {set_clause} WHERE id = ?",

                values + [d["id"]]

            )

            updated += 1

        else:

            conn.execute(

                f"INSERT INTO sessions ({fields_str}) VALUES ({placeholders})",

                values

            )

            added += 1

    conn_src.close()

    tmp_db.unlink()

    recompute_aggregates_full(conn)

    set_watermark(conn, max_ts)

    return added, updated

# ── Aggregation ────────────────────────────────────────────────────

def recompute_aggregates_full(conn):

    """DELETE + re-INSERT all aggregates (used for full refresh)."""

    conn.execute("DELETE FROM daily_stats")

    conn.execute("""

        INSERT INTO daily_stats (date, session_count, message_count,

            input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,

            reasoning_tokens, total_tokens, estimated_cost_usd, models_used, sources_used)

        SELECT date, COUNT(*), SUM(message_count),

            SUM(input_tokens), SUM(output_tokens),

            SUM(cache_read_tokens), SUM(cache_write_tokens),

            SUM(reasoning_tokens), SUM(total_tokens),

            SUM(COALESCE(estimated_cost_usd, 0)),

            json_group_array(DISTINCT model), json_group_array(DISTINCT source)

        FROM sessions GROUP BY date

    """)

    conn.execute("DELETE FROM model_stats")

    conn.execute("""

        INSERT INTO model_stats (model, session_count,

            input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,

            reasoning_tokens, total_tokens, estimated_cost_usd, last_used)

        SELECT model, COUNT(*), SUM(input_tokens), SUM(output_tokens),

            SUM(cache_read_tokens), SUM(cache_write_tokens),

            SUM(reasoning_tokens), SUM(total_tokens),

            SUM(COALESCE(estimated_cost_usd, 0)), MAX(started_at)

        FROM sessions WHERE model IS NOT NULL GROUP BY model

    """)

    conn.commit()

def recompute_aggregates_incremental(conn):

    """Fast path: update only affected dates/models."""

    # Get dates that have new/updated sessions

    affected_dates = conn.execute("""

        SELECT DISTINCT date FROM sessions

        WHERE date NOT IN (SELECT date FROM daily_stats)

           OR id IN (SELECT id FROM sessions WHERE date IN (SELECT date FROM daily_stats))

    """).fetchall()

    affected_date_list = [r[0] for r in affected_dates]

    if affected_date_list:

        placeholders = ",".join("?" * len(affected_date_list))

        conn.execute(f"DELETE FROM daily_stats WHERE date IN ({placeholders})", affected_date_list)

        conn.execute(f"""

            INSERT INTO daily_stats (date, session_count, message_count,

                input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,

                reasoning_tokens, total_tokens, estimated_cost_usd, models_used, sources_used)

            SELECT date, COUNT(*), SUM(message_count),

                SUM(input_tokens), SUM(output_tokens),

                SUM(cache_read_tokens), SUM(cache_write_tokens),

                SUM(reasoning_tokens), SUM(total_tokens),

                SUM(COALESCE(estimated_cost_usd, 0)),

                json_group_array(DISTINCT model), json_group_array(DISTINCT source)

            FROM sessions

            WHERE date IN ({placeholders})

            GROUP BY date

        """, affected_date_list)

    # Model stats: simpler to full-rebuild (few rows, fast)

    conn.execute("DELETE FROM model_stats")

    conn.execute("""

        INSERT INTO model_stats (model, session_count,

            input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,

            reasoning_tokens, total_tokens, estimated_cost_usd, last_used)

        SELECT model, COUNT(*), SUM(input_tokens), SUM(output_tokens),

            SUM(cache_read_tokens), SUM(cache_write_tokens),

            SUM(reasoning_tokens), SUM(total_tokens),

            SUM(COALESCE(estimated_cost_usd, 0)), MAX(started_at)

        FROM sessions WHERE model IS NOT NULL GROUP BY model

    """)

    conn.commit()

# ── OpenRouter credits ─────────────────────────────────────────────

def fetch_credits(api_key):

    url = f"{OPENROUTER_BASE}/credits"

    headers = {"Authorization": f"Bearer {api_key}"}

    try:

        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 200:

            data = resp.json().get("data", {})

            return {"total_credits": data.get("total_credits", 0),

                    "total_usage": data.get("total_usage", 0)}

        else:

            print(f"[WARN] OpenRouter credits: HTTP {resp.status_code}")

            return None

    except Exception as e:

        print(f"[WARN] Credits fetch failed: {e}")

        return None

def save_credits(conn, credits):

    conn.execute(

        "INSERT OR REPLACE INTO account_snapshots (timestamp, total_credits, total_usage) VALUES (?, ?, ?)",

        (time.time(), credits["total_credits"], credits["total_usage"])

    )

    conn.commit()

    return 1

# ── Run log ────────────────────────────────────────────────────────

def log_run_start(conn):

    cur = conn.execute(

        "INSERT INTO collector_runs (started_at, status) VALUES (?, 'running')",

        (time.time(),)

    )

    conn.commit()

    return cur.lastrowid

def log_run_end(conn, run_id, status, sessions_added=0, sessions_updated=0,

                credits_fetched=0, error=None):

    conn.execute(

        """UPDATE collector_runs

           SET ended_at = ?, status = ?, sessions_added = ?,

               sessions_updated = ?, credits_fetched = ?, error_message = ?

           WHERE id = ?""",

        (time.time(), status, sessions_added, sessions_updated,

         credits_fetched, error, run_id)

    )

    conn.commit()

# ── Main ───────────────────────────────────────────────────────────

def main():

    parser = argparse.ArgumentParser(description="Hermes Dashboard Collector v2")

    parser.add_argument("--sessions-only", action="store_true")

    parser.add_argument("--credits-only", action="store_true")

    parser.add_argument("--full-refresh", action="store_true",

                        help="Full rebuild of all aggregations")

    args = parser.parse_args()

    config = load_config()

    global HERMES_DIR, STATE_DB, AUTH_JSON

    config_hermes = config.get("hermes_dir")

    if config_hermes:

        HERMES_DIR = _find_hermes_dir(config_hermes)

        if HERMES_DIR:

            STATE_DB = HERMES_DIR / "state.db"

            AUTH_JSON = HERMES_DIR / "auth.json"

    conn = sqlite3.connect(str(DB_PATH))

    init_db(conn)

    migrate_db(conn)

    run_id = log_run_start(conn)

    sessions_added = sessions_updated = credits_fetched = 0

    status = "success"

    error_msg = None

    try:

        do_sessions = not args.credits_only

        if do_sessions:

            wm = get_watermark(conn)

            if args.full_refresh:

                print(f"[collector] Full refresh...")

                sessions_added, sessions_updated = collect_sessions_full(conn)

            else:

                print(f"[collector] Incremental (since {wm:.0f} = {time.strftime('%Y-%m-%d %H:%M', time.localtime(wm)) if wm else 'beginning'})...")

                sessions_added, sessions_updated = collect_sessions_incremental(conn)

            print(f"[collector] Sessions: {sessions_added} new, {sessions_updated} updated")

            # Calculate real costs based on latest model prices

            compute_real_costs(conn)

            # Collect tool usage and errors from state.db

            collect_tool_performance(conn)

            # Collect system events (empty responses, rate limits) from state.db
            collect_system_events(conn)

        if not args.sessions_only:

            api_key = get_api_key()

            if api_key:

                print("[collector] Fetching OpenRouter credits...")

                credits = fetch_credits(api_key)

                if credits:

                    credits_fetched = save_credits(conn, credits)

                    print(f"[collector] Credits: ${credits['total_usage']:.2f} / ${credits['total_credits']:.2f}")

                    # Fetch model prices for real cost calculation

                    fetch_model_prices(conn, api_key)

# Fetch model prices for real cost calculation

                    collect_openrouter_activity(conn)  # token comparison (requires management key)

                else:

                    print("[collector] Credits unavailable")

            else:

                print("[collector] No API key — skipping credits")

        # Summary

        total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

        cost = conn.execute("SELECT SUM(COALESCE(estimated_cost_usd, 0)) FROM sessions").fetchone()[0] or 0

        latest = conn.execute("SELECT MAX(date) FROM sessions").fetchone()[0] or "N/A"

        last_credit = conn.execute(

            "SELECT total_usage, total_credits FROM account_snapshots ORDER BY timestamp DESC LIMIT 1"

        ).fetchone()

        credit_line = ""

        if last_credit:

            credit_line = f" | OpenRouter: ${last_credit[0]:.2f} / ${last_credit[1]:.2f}"

        print(f"[collector] Dashboard: {total} sessions, ${cost:.4f} est, latest {latest}{credit_line}")

    except Exception as e:

        status = "error"

        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

        print(f"[collector] ERROR: {error_msg}", file=sys.stderr)

    finally:

        log_run_end(conn, run_id, status, sessions_added, sessions_updated,

                    credits_fetched, error_msg)

        conn.close()

def compute_real_costs(conn):

    """

    Calculate real costs for sessions based on latest model prices.

    Updates sessions.actual_cost_calculated, price_source, and cost_discrepancy.

    Returns number of sessions updated.

    """

    cursor = conn.cursor()

    # Get latest prices for each model

    cursor.execute("""

        SELECT model_id, input_price, output_price, cache_read_price, cache_write_price, reasoning_price

        FROM model_prices 

        WHERE timestamp = (SELECT MAX(timestamp) FROM model_prices WHERE model_id = model_prices.model_id)

        AND (input_price IS NOT NULL OR output_price IS NOT NULL)

    """)

    price_map = {}

    for row in cursor.fetchall():

        model_id, input_price, output_price, cache_read_price, cache_write_price, reasoning_price = row

        price_map[model_id] = {

            'input': input_price or 0.0,

            'output': output_price or 0.0,

            'cache_read': cache_read_price or 0.0,

            'cache_write': cache_write_price or 0.0,

            'reasoning': reasoning_price or 0.0

        }

    if not price_map:

        print("[compute_real_costs] No model prices available, skipping")

        return 0

    print(f"[compute_real_costs] Using prices for {len(price_map)} models")

    # Get sessions that need real cost calculation

    cursor.execute("""

        SELECT id, model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, 

               estimated_cost_usd, actual_cost_calculated

        FROM sessions 

        WHERE model IS NOT NULL 

        AND (actual_cost_calculated IS NULL OR price_source IS NULL)

        AND input_tokens + output_tokens + cache_read_tokens + cache_write_tokens + reasoning_tokens > 0

    """)

    sessions = cursor.fetchall()

    print(f"[compute_real_costs] Found {len(sessions)} sessions needing real cost calculation")

    updated = 0

    for session in sessions:

        session_id, model, input_tokens, output_tokens, cache_read, cache_write, reasoning, estimated_cost, actual_cost = session

        # Try exact model match first

        prices = price_map.get(model)

        # If not found, try to match by prefix (e.g., "deepseek/deepseek-v4-pro" might be "deepseek/deepseek-v4-pro:free")

        if not prices:

            for model_key in price_map:

                if model_key.startswith(model) or model.startswith(model_key):

                    prices = price_map[model_key]

                    break

        if not prices:

            # No price for this model

            continue

        # Calculate actual cost (prices from API are per token, no division needed)

        actual_cost = (

            (input_tokens * prices['input']) +

            (output_tokens * prices['output']) +

            (cache_read * prices['cache_read']) +

            (cache_write * prices['cache_write']) +

            (reasoning * prices['reasoning'])

        )

        # Calculate discrepancy if estimated cost exists

        discrepancy = None

        if estimated_cost is not None and estimated_cost > 0:

            discrepancy = actual_cost - estimated_cost

        # Update session

        cursor.execute("""

            UPDATE sessions 

            SET actual_cost_calculated = ?, 

                price_source = 'openrouter_api_v1_models',

                cost_discrepancy = ?

            WHERE id = ?

        """, (actual_cost, discrepancy, session_id))

        updated += 1

    conn.commit()

    print(f"[compute_real_costs] Updated {updated} sessions with real costs")

    return updated

# ── State DB helpers (recovered from original) ──

def safe_copy_state_db():

    """Copy state.db to a temp file (WAL-safe: gateway keeps the real one locked)."""

    global STATE_DB

    src = STATE_DB

    if not src or not src.exists():

        print("[safe_copy_state_db] No state.db found, skipping")

        return None

    dst = src.with_suffix('.db.collector_tmp')

    try:

        shutil.copy2(str(src), str(dst))

        return dst

    except Exception as e:

        print(f"[safe_copy_state_db] Copy failed: {e}")

        return None

def get_watermark(conn):

    """Return the high-water mark (last processed session started_at), or 0."""

    row = conn.execute(

        "SELECT value FROM high_water_mark WHERE key = 'last_session_started_at'"

    ).fetchone()

    return row[0] if row else 0.0

def set_watermark(conn, ts):

    """Update the high-water mark."""

    conn.execute(

        "INSERT OR REPLACE INTO high_water_mark (key, value, updated_at) VALUES (?, ?, ?)",

        ('last_session_started_at', ts, time.time())

    )

    conn.commit()

def collect_tool_performance(conn):

    """

    Populate tool_usage and errors_log from state.db messages.\nParses tool_calls JSON from assistant messages and checks tool results for errors.\n    """

    tmp_db = safe_copy_state_db()

    if not tmp_db:

        return 0, 0

    conn_src = sqlite3.connect(str(tmp_db))

    conn_src.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Last watermark

    last_ts = conn.execute(

        "SELECT COALESCE(MAX(timestamp), 0) FROM tool_usage"

    ).fetchone()[0]

    # Parse assistant messages with tool_calls

    rows = conn_src.execute(

        "SELECT session_id, tool_calls, timestamp FROM messages "

        "WHERE role = 'assistant' AND finish_reason = 'tool_calls' "

        "AND tool_calls IS NOT NULL AND timestamp > ? ORDER BY timestamp",

        (last_ts,)

    ).fetchall()

    # Parse tool result messages for errors

    tool_rows = conn_src.execute(

        "SELECT session_id, content, timestamp FROM messages "

        "WHERE role = 'tool' AND timestamp > ? ORDER BY timestamp",

        (last_ts,)

    ).fetchall()

    # Build error lookup per session

    session_errors = {}

    for r in tool_rows:

        d = dict(r)

        content = d.get('content', '')

        sid = d['session_id']

        try:

            result = json.loads(content) if isinstance(content, str) else {}

        except (json.JSONDecodeError, TypeError):

            result = {}

        if isinstance(result, dict):

            exit_code = result.get('exit_code')

            error = result.get('error')

            if error or (exit_code is not None and exit_code != 0):

                if sid not in session_errors:

                    session_errors[sid] = []

                err_msg = str(error or 'exit_' + str(exit_code))[:200]

                session_errors[sid].append(err_msg)

    # Insert tool usages

    tools_inserted = 0

    for r in rows:

        d = dict(r)

        tc_str = d.get('tool_calls', '[]')

        sid = d['session_id']

        ts = d['timestamp']

        try:

            calls = json.loads(tc_str) if isinstance(tc_str, str) else []

        except (json.JSONDecodeError, TypeError):

            calls = []

        if not isinstance(calls, list):

            calls = [calls] if calls else []

        for call in calls:

            fn = call.get('function', {})

            tool_name = fn.get('name', 'unknown')

            args_str = fn.get('arguments', '{}')[:500]

            existing = conn.execute(

                "SELECT id FROM tool_usage WHERE session_id=? AND tool_name=? AND timestamp=?",

                (sid, tool_name, ts)

            ).fetchone()

            if existing:

                continue

            # Check if session has errors near this timestamp

            sess_errs = session_errors.get(sid, [])

            success = len(sess_errs) == 0

            err_msg = sess_errs[0] if sess_errs else None

            cursor.execute(

                "INSERT INTO tool_usage (session_id, tool_name, timestamp, success, error_message, arguments) "

                "VALUES (?, ?, ?, ?, ?, ?)",

                (sid, tool_name, ts, success, err_msg, args_str)

            )

            tools_inserted += 1

    # Insert errors into errors_log

    errors_inserted = 0

    for sid, errs in session_errors.items():

        for err_msg in errs:

            ts = conn_src.execute(

                "SELECT MIN(timestamp) FROM messages WHERE session_id=? AND role='tool' "

                "AND content LIKE ?", (sid, f'%{err_msg[:50]}%')

            ).fetchone()[0] or time.time()

            existing = conn.execute(

                "SELECT id FROM errors_log WHERE session_id=? AND message=?",

                (sid, err_msg)

            ).fetchone()

            if not existing:

                cursor.execute(

                    "INSERT INTO errors_log (timestamp, source, error_type, message, session_id) "

                    "VALUES (?, ?, ?, ?, ?)",

                    (ts, 'state_db', 'tool_error', err_msg, sid)

                )

                errors_inserted += 1

    conn.commit()

    conn_src.close()

    tmp_db.unlink()

    print(f"[collect_tool_performance] Inserted {tools_inserted} tool usages, {errors_inserted} errors")

    return tools_inserted, errors_inserted


def collect_openrouter_activity(conn):

    """

    Fetch daily token usage per model from OpenRouter /api/v1/activity.

    Requires management key. If not available, logs warning and skips.

    Returns (rows_inserted, rows_updated).

    """

    management_key = get_management_key()

    if not management_key:

        print("[collect_openrouter_activity] No management key — add OPENROUTER_MANAGEMENT_KEY to .env. Skipping.")

        return 0, 0

        print("[collect_openrouter_activity] No API key, skipping")

        return 0, 0

    # Fetch high‑water mark ‑ last collected date (as Unix timestamp)

    cursor = conn.cursor()

    row = cursor.execute(

        "SELECT value FROM high_water_mark WHERE key = 'last_openrouter_activity_date'"

    ).fetchone()

    last_collected_date = row[0] if row else 0.0  # stored as YYYY‑MM‑DD string? Let's store as timestamp of earliest date

    # Convert to datetime

    import time, datetime, requests, json

    # For now, we'll just fetch all data and upsert.

    headers = {'Authorization': f'Bearer {management_key}', 'User-Agent': 'Hermes-Dashboard/1.0'}

    try:

        resp = requests.get('https://openrouter.ai/api/v1/activity', headers=headers, timeout=30)

        if resp.status_code == 403:

            print("[collect_openrouter_activity] 403 Forbidden — need management key. Skipping.")

            return 0, 0

        resp.raise_for_status()

        data = resp.json()

    except Exception as e:

        print(f"[collect_openrouter_activity] Failed to fetch activity: {e}")

        return 0, 0

    if 'data' not in data:

        print("[collect_openrouter_activity] No data field in response")

        return 0, 0

    rows_inserted = 0

    rows_updated = 0

    for entry in data['data']:

        date = entry.get('date')

        model = entry.get('model')

        endpoint_id = entry.get('endpoint_id')

        prompt_tokens = entry.get('prompt_tokens', 0)

        completion_tokens = entry.get('completion_tokens', 0)

        reasoning_tokens = entry.get('reasoning_tokens', 0)

        requests_count = entry.get('requests', 0)

        usage_credits = entry.get('usage', 0.0)

        provider_name = entry.get('provider_name')

        model_permaslug = entry.get('model_permaslug')

        byok_usage_inference = entry.get('byok_usage_inference', 0.0)

        collected_at = time.time()

        # Upsert

        cursor.execute("""

            INSERT INTO openrouter_daily_usage 

            (date, model, endpoint_id, prompt_tokens, completion_tokens, reasoning_tokens,

             requests, usage, provider_name, model_permaslug, byok_usage_inference, collected_at)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(date, model, endpoint_id) DO UPDATE SET

                prompt_tokens = excluded.prompt_tokens,

                completion_tokens = excluded.completion_tokens,

                reasoning_tokens = excluded.reasoning_tokens,

                requests = excluded.requests,

                usage = excluded.usage,

                provider_name = excluded.provider_name,

                model_permaslug = excluded.model_permaslug,

                byok_usage_inference = excluded.byok_usage_inference,

                collected_at = excluded.collected_at

        """, (date, model, endpoint_id, prompt_tokens, completion_tokens, reasoning_tokens,

              requests_count, usage_credits, provider_name, model_permaslug, byok_usage_inference, collected_at))

        rows_inserted += 1

    # Update high‑water mark (use latest date? we'll keep as timestamp)

    latest_date = max([e.get('date') for e in data['data']]) if data['data'] else None

    if latest_date:

        # Convert date string to Unix timestamp (midnight)

        import datetime as dt

        dt_obj = dt.datetime.strptime(latest_date, '%Y-%m-%d')

        timestamp = dt_obj.timestamp()

        cursor.execute(

            "UPDATE high_water_mark SET value = ?, updated_at = ? WHERE key = 'last_openrouter_activity_date'",

            (timestamp, time.time())

        )

    conn.commit()

    print(f"[collect_openrouter_activity] Inserted/updated {rows_inserted} rows")

    return rows_inserted, rows_updated

def collect_system_events(conn):
    """
    Capture 'Empty response', 'model returned empty', 'Rate limited' and 
    'switching to fallback' events from state.db messages into errors_log.
    These are system-level events NOT captured by collect_tool_performance().
    """
    tmp_db = safe_copy_state_db()
    if not tmp_db:
        return 0

    conn_src = sqlite3.connect(str(tmp_db))
    conn_src.row_factory = sqlite3.Row

    # Last processed timestamp from errors_log (source='state_db_events')
    last_ts = conn.execute(
        "SELECT COALESCE(MAX(timestamp), 0) FROM errors_log WHERE source = 'state_db_events'"
    ).fetchone()[0]

    cursor = conn.cursor()
    rows_inserted = 0

    # --- Pattern 1: Empty response / nudging events (injected as user messages) ---
    patterns_empty = {
        'empty_response': "You just executed tool calls but returned an empty response",
        'model_returned_empty': "Model returned empty after tool calls",
        'nudging_to_continue': "nudging to continue",
    }

    for error_type, pattern in patterns_empty.items():
        rows = conn_src.execute(
            "SELECT session_id, content, timestamp FROM messages "
            "WHERE role = 'user' AND content LIKE ? AND timestamp > ? ORDER BY timestamp",
            (f"%{pattern}%", last_ts)
        ).fetchall()

        for row in rows:
            cursor.execute(
                "INSERT OR IGNORE INTO errors_log "
                "(timestamp, source, error_type, message, session_id, tool_name, resolved) "
                "VALUES (?, ?, ?, ?, ?, ?, 0)",
                (row['timestamp'], 'state_db_events', error_type,
                 f"Empty response: {str(row['content'])[:200]}", row['session_id'], None)
            )
            rows_inserted += 1

    # --- Pattern 2: Previous turn interrupted ---
    rows = conn_src.execute(
        "SELECT session_id, content, timestamp FROM messages "
        "WHERE role = 'user' AND content LIKE '%previous turn was interrupted%' "
        "AND timestamp > ? ORDER BY timestamp",
        (last_ts,)
    ).fetchall()

    for row in rows:
        cursor.execute(
            "INSERT OR IGNORE INTO errors_log "
            "(timestamp, source, error_type, message, session_id, tool_name, resolved) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            (row['timestamp'], 'state_db_events', 'previous_turn_interrupted',
             f"Previous turn interrupted: {str(row['content'])[:200]}", row['session_id'], None)
        )
        rows_inserted += 1

    # --- Pattern 3: Rate limited / switching to fallback ---
    patterns_rate = {
        'rate_limit': "Rate limited",
        'switching_fallback': "switching to fallback",
        'primary_model_failed': "Primary model failed",
    }

    for error_type, pattern in patterns_rate.items():
        rows = conn_src.execute(
            "SELECT session_id, content, timestamp FROM messages "
            "WHERE (role = 'assistant' OR role = 'user') AND content LIKE ? AND timestamp > ? ORDER BY timestamp",
            (f"%{pattern}%", last_ts)
        ).fetchall()

        for row in rows:
            cursor.execute(
                "INSERT OR IGNORE INTO errors_log "
                "(timestamp, source, error_type, message, session_id, tool_name, resolved) "
                "VALUES (?, ?, ?, ?, ?, ?, 0)",
                (row['timestamp'], 'state_db_events', error_type,
                 f"Rate limit/fallback: {str(row['content'])[:200]}", row['session_id'], None)
            )
            rows_inserted += 1

    conn.commit()
    conn_src.close()

    if rows_inserted > 0:
        print(f"[collect_system_events] Inserted {rows_inserted} system events (empty responses + rate limits)")

    # Clean up temp db
    try:
        tmp_db.unlink()
    except Exception:
        pass

    return rows_inserted

if __name__ == "__main__":

    sys.exit(main())

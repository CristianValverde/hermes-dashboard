"""Hermes Dashboard API — Flask backend serving real data from dashboard.db"""
import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory

from agent_log_metrics import parse_agent_log_metrics
from economic_classes import build_economic_breakdown, build_provider_usage_breakdown, get_provider_catalog

app = Flask(__name__, static_folder='static')

# Register MIME types for JSX files (Babel standalone needs correct MIME)
import mimetypes
mimetypes.add_type('text/javascript', '.jsx')
mimetypes.add_type('text/javascript', '.mjs')

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard.db")

COLLECTOR_PATH = os.path.join(os.path.dirname(__file__), "..", "collector.py")


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_dashboard_runtime():
    access_mode = (os.getenv("HERMES_DASHBOARD_ACCESS_MODE") or "").strip().lower()
    host = (os.getenv("HERMES_DASHBOARD_HOST") or "").strip()

    if not host:
        host = "0.0.0.0" if access_mode == "network" else "127.0.0.1"

    port_value = (os.getenv("HERMES_DASHBOARD_PORT") or "8590").strip()
    try:
        port = int(port_value)
    except ValueError:
        print(f"[dashboard] Invalid HERMES_DASHBOARD_PORT={port_value!r}; using 8590")
        port = 8590

    debug = env_flag("HERMES_DASHBOARD_DEBUG", True)
    network_enabled = host not in {"127.0.0.1", "localhost", "::1"}

    return {
        "access_mode": access_mode or ("network" if network_enabled else "localhost"),
        "host": host,
        "port": port,
        "debug": debug,
        "network_enabled": network_enabled,
        "local_url": f"http://localhost:{port}",
    }


def print_startup_summary(config):
    print("Hermes Dashboard running")
    print(f"- Local:   {config['local_url']}")
    print(f"- Network: {'enabled' if config['network_enabled'] else 'disabled'}")

    if config["network_enabled"]:
        print(
            "Warning: dashboard is reachable from LAN/VPN. "
            "Do not expose to public internet without auth/HTTPS."
        )


def run_collector():
    """Run collector via subprocess before serving the dashboard.

    Ensures data is always fresh on dashboard open. Replaces hourly cron.
    Runs incrementally - typically <3s for recent sessions.
    """
    import subprocess, sys
    python = sys.executable
    start = time.time()
    print("[collector] Running...", end=" ", flush=True)
    try:
        result = subprocess.run(
            [python, COLLECTOR_PATH],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(COLLECTOR_PATH),
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            print(f"done in {elapsed:.1f}s")
        else:
            print(f"exit {result.returncode} in {elapsed:.1f}s")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-3:]:
                    print(f"  ! {line}")
    except subprocess.TimeoutExpired:
        print(f"timed out after 120s")
    except Exception as e:
        print(f"error: {e}")


AGENT_LOG_PATH = os.path.expanduser("~/AppData/Local/hermes/logs/agent.log")


def load_agent_log_metrics():
    """Parse agent.log for global response latency metrics."""
    return parse_agent_log_metrics(AGENT_LOG_PATH)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fmt_date(ts):
    if ts is None: return u'—'
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')


def fmt_date_short(ts):
    if ts is None: return u'—'
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')


MODEL_COLORS = ['#00D4B4', '#A855F7', '#39D966', '#E84848', '#FBBF24', '#06B6D4', '#EC4899', '#8B5CF6', '#34D399', '#22D3EE', '#FF6B6B', '#A78BFA']

TOOL_COLORS = ['#00D4B4', '#A855F7', '#39D966', '#E84848', '#FBBF24', '#06B6D4', '#EC4899', '#8B5CF6', '#34D399', '#22D3EE', '#FF6B6B', '#A78BFA']


def load_overview_extras(conn):
    """Avg session duration, active models (last 5 sessions)."""
    c = conn.cursor()
    # Active models in last 5 completed sessions
    c.execute("""
        SELECT DISTINCT model FROM sessions 
        WHERE ended_at IS NOT NULL AND model IS NOT NULL
        ORDER BY ended_at DESC LIMIT 5
    """)
    active_models = [r['model'] for r in c.fetchall()]
    
    # Avg session duration (completed sessions only)
    c.execute("""
        SELECT ROUND(AVG(ended_at - started_at), 0) as avg_duration,
               COUNT(*) as completed_sessions
        FROM sessions WHERE ended_at IS NOT NULL AND started_at IS NOT NULL
    """)
    r = dict(c.fetchone())
    
    return {
        'activeModels': active_models,
        'avgSessionDuration': r['avg_duration'] or 0,
        'completedSessions': r['completed_sessions'] or 0,
    }


def load_totals(conn):
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) as sessions,
               COALESCE(SUM(input_tokens), 0) as input_tokens,
               COALESCE(SUM(output_tokens), 0) as output_tokens,
               COALESCE(SUM(cache_read_tokens), 0) as cache_read,
               COALESCE(SUM(cache_write_tokens), 0) as cache_write,
               COALESCE(SUM(reasoning_tokens), 0) as reasoning,
               COUNT(DISTINCT model) as models,
               COALESCE(SUM(tool_call_count), 0) as tool_calls
        FROM sessions
    """)
    row = dict(c.fetchone())
    totals = row
    totals['tokens'] = totals['input_tokens'] + totals['output_tokens'] + totals['cache_read'] + totals['cache_write'] + totals['reasoning']
    c.execute("SELECT COUNT(DISTINCT date(started_at, 'unixepoch')) as days FROM sessions WHERE started_at IS NOT NULL")
    totals['daysActive'] = dict(c.fetchone())['days']
    return totals


def load_models(conn):
    c = conn.cursor()
    c.execute("""
        SELECT model, COUNT(*) as session_count,
               COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens + reasoning_tokens), 0) as total_tokens,
               COALESCE(SUM(estimated_cost_usd), 0) as total_cost
        FROM sessions WHERE model IS NOT NULL
        GROUP BY model ORDER BY total_tokens DESC
    """)
    models = []
    for i, row in enumerate(c.fetchall()):
        r = dict(row)
        short = r['model'].split('/')[-1].split(':')[0][:12].upper() if '/' in r['model'] else r['model'][:12].upper()
        models.append({
            'id': r['model'], 'short': short, 'color': MODEL_COLORS[i % len(MODEL_COLORS)],
            'session_count': r['session_count'], 'total_tokens': r['total_tokens'], 'total_cost': r['total_cost'],
        })
    return models


def load_economic_breakdown(conn):
    c = conn.cursor()
    c.execute("""
        SELECT billing_provider,
               COALESCE(SUM(
                   COALESCE(input_tokens, 0) +
                   COALESCE(output_tokens, 0) +
                   COALESCE(cache_read_tokens, 0) +
                   COALESCE(cache_write_tokens, 0) +
                   COALESCE(reasoning_tokens, 0)
               ), 0) as total_tokens
        FROM sessions
        GROUP BY billing_provider
    """)
    return build_economic_breakdown([dict(r) for r in c.fetchall()])


def load_economic_provider_usage(conn):
    c = conn.cursor()
    c.execute("""
        SELECT billing_provider,
               COUNT(*) as session_count,
               GROUP_CONCAT(DISTINCT model) as models,
               COALESCE(SUM(
                   COALESCE(input_tokens, 0) +
                   COALESCE(output_tokens, 0) +
                   COALESCE(cache_read_tokens, 0) +
                   COALESCE(cache_write_tokens, 0) +
                   COALESCE(reasoning_tokens, 0)
               ), 0) as total_tokens
        FROM sessions
        GROUP BY billing_provider
    """)
    return build_provider_usage_breakdown([dict(r) for r in c.fetchall()])


def load_tokens_per_day(conn, models):
    c = conn.cursor()
    c.execute("SELECT MIN(started_at) as min_ts, MAX(started_at) as max_ts FROM sessions WHERE started_at IS NOT NULL")
    range_row = c.fetchone()
    if not range_row or not range_row['min_ts']:
        return []
    min_date = datetime.fromtimestamp(range_row['min_ts']).date()
    max_date = datetime.fromtimestamp(range_row['max_ts']).date()
    days_list = [(min_date + timedelta(days=i)).isoformat() for i in range((max_date - min_date).days + 1)]
    c.execute("""
        SELECT date(started_at, 'unixepoch') as day, model,
               COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens + reasoning_tokens), 0) as tokens
        FROM sessions WHERE started_at IS NOT NULL AND model IS NOT NULL
        GROUP BY day, model ORDER BY day
    """)
    day_model_data = {}
    for row in c.fetchall():
        r = dict(row)
        day_model_data.setdefault(r['day'], {})[r['model']] = r['tokens']
    return [{'date': d, **{m['id']: day_model_data.get(d, {}).get(m['id'], 0) for m in models}} for d in days_list]


def load_tools(conn):
    c = conn.cursor()
    c.execute("""
        SELECT tool_name, COUNT(*) as count,
               ROUND(CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 1) as success_rate,
               ROUND(AVG(duration_ms), 0) as avg_duration
        FROM tool_usage GROUP BY tool_name ORDER BY count DESC
    """)
    tools = []
    for i, r in enumerate(c.fetchall()):
        rd = dict(r)
        tools.append({'name': rd['tool_name'], 'count': rd['count'],
                      'success': rd['success_rate'] / 100.0, 'durMs': rd['avg_duration'],
                      'color': TOOL_COLORS[i % len(TOOL_COLORS)]})

    # Daily tool usage (last 30 days)
    c.execute("""
        SELECT date(timestamp, 'unixepoch') as day, tool_name, COUNT(*) as count
        FROM tool_usage WHERE timestamp IS NOT NULL
        GROUP BY day, tool_name ORDER BY day
    """)
    daily = {}
    for r in c.fetchall():
        rd = dict(r)
        daily.setdefault(rd['day'], {})
        daily[rd['day']][rd['tool_name']] = rd['count']

    return {'tools': tools, 'daily': daily}


def load_tool_token_usage(conn):
    """Attribute session tokens across tool calls in the same session."""
    c = conn.cursor()
    c.execute("""
        WITH session_tool_counts AS (
            SELECT session_id, COUNT(*) as actual_tool_calls
            FROM tool_usage
            GROUP BY session_id
        ),
        session_tokens AS (
            SELECT id as session_id,
                   COALESCE(input_tokens, 0) +
                   COALESCE(output_tokens, 0) +
                   COALESCE(cache_read_tokens, 0) +
                   COALESCE(cache_write_tokens, 0) +
                   COALESCE(reasoning_tokens, 0) as tokens
            FROM sessions
        )
        SELECT tu.tool_name,
               COUNT(*) as calls,
               COUNT(DISTINCT tu.session_id) as sessions,
               COALESCE(SUM(CAST(st.tokens AS REAL) / NULLIF(stc.actual_tool_calls, 0)), 0) as attributed_tokens,
               ROUND(CAST(SUM(CASE WHEN tu.success = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 1) as success_rate
        FROM tool_usage tu
        JOIN session_tool_counts stc ON stc.session_id = tu.session_id
        JOIN session_tokens st ON st.session_id = tu.session_id
        GROUP BY tu.tool_name
        ORDER BY attributed_tokens DESC
    """)
    rows = []
    for i, r in enumerate(c.fetchall()):
        rd = dict(r)
        rows.append({
            'name': rd['tool_name'],
            'tokens': int(round(rd['attributed_tokens'] or 0)),
            'calls': rd['calls'] or 0,
            'sessions': rd['sessions'] or 0,
            'success': (rd['success_rate'] or 0) / 100.0,
            'color': TOOL_COLORS[i % len(TOOL_COLORS)],
        })
    return rows


def load_sources(conn):
    c = conn.cursor()
    c.execute("SELECT source, COUNT(*) as count FROM sessions WHERE source IS NOT NULL GROUP BY source ORDER BY count DESC")
    source_colors = {'telegram': '#00D4B4', 'cli': '#A855F7', 'api': '#06B6D4'}
    return [{'name': dict(r)['source'], 'count': dict(r)['count'],
             'color': source_colors.get(dict(r)['source'], TOOL_COLORS[i % len(TOOL_COLORS)])}
            for i, r in enumerate(c.fetchall())]


def load_recent_sessions(conn, limit=10):
    c = conn.cursor()
    c.execute("""
        SELECT id, started_at, model, source, message_count as msgs,
               tool_call_count as tools,
               COALESCE(input_tokens + output_tokens + cache_read_tokens + cache_write_tokens + reasoning_tokens, 0) as tokens,
               COALESCE(actual_cost_calculated, estimated_cost_usd, 0) as cost
        FROM sessions WHERE started_at IS NOT NULL
        ORDER BY started_at DESC LIMIT ?
    """, (limit,))
    return [{'id': (dict(r)['id'][:4] + '..' + dict(r)['id'][-4:]) if len(dict(r)['id']) > 10 else dict(r)['id'],
             'started': fmt_date(dict(r)['started_at']), 'model': dict(r)['model'] or u'—',
             'source': dict(r)['source'] or u'—', 'msgs': dict(r)['msgs'],
             'tools': dict(r)['tools'], 'tokens': dict(r)['tokens'], 'cost': round(dict(r)['cost'], 2)}
            for r in c.fetchall()]


def load_errors(conn):
    c = conn.cursor()
    c.execute("""
        SELECT error_type, COUNT(*) as total,
               COUNT(DISTINCT source) as source_count,
               MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
        FROM errors_log GROUP BY error_type ORDER BY total DESC LIMIT 20
    """)
    errors = []
    for row in c.fetchall():
        r = dict(row)
        priority = round(r['total'] * 1.5, 1)
        c2 = conn.cursor()
        c2.execute("SELECT DISTINCT source FROM errors_log WHERE error_type = ? AND source IS NOT NULL LIMIT 5", (r['error_type'],))
        src_list = [row2['source'] for row2 in c2.fetchall()]
        errors.append({
            'pattern': r['error_type'], 'total': r['total'], 'sources': ','.join(src_list) if src_list else 'system',
            'firstSeen': fmt_date_short(r['first_seen']), 'lastSeen': fmt_date_short(r['last_seen']),
            'priority': priority,
        })
    return errors


def load_error_trend(conn):
    c = conn.cursor()
    c.execute("""
        SELECT date(timestamp, 'unixepoch') as day,
               CASE
                   WHEN error_type LIKE '%tool%' THEN 'tool_failure'
                   WHEN error_type LIKE '%empty%' OR error_type LIKE '%nudge%' OR error_type LIKE '%model%' THEN 'model_behavior'
                   WHEN error_type LIKE '%fallback%' OR error_type LIKE '%primary%' OR error_type LIKE '%rate%limit%' THEN 'provider'
                   WHEN error_type LIKE '%interrupt%' THEN 'user_interrupt'
                   ELSE 'other'
               END as category, COUNT(*) as count
        FROM errors_log WHERE timestamp IS NOT NULL
        GROUP BY day, category ORDER BY day
    """)
    cats = ['tool_failure', 'model_behavior', 'provider', 'user_interrupt', 'other']
    day_data = {}
    for row in c.fetchall():
        r = dict(row)
        day_data.setdefault(r['day'], {c: 0 for c in cats})
        day_data[r['day']][r['category']] = r['count']
    return [{'date': d, **day_data[d]} for d in sorted(day_data.keys())]


def load_sessions_analytics(conn):
    """Per-session analytics: avg tokens, generation throughput, duration, tools, models used."""
    c = conn.cursor()
    
    # Aggregate per-session averages
    c.execute("""
        SELECT 
            COUNT(*) as total_sessions,
            ROUND(AVG(ended_at - started_at), 0) as avg_duration_s,
            ROUND(AVG(input_tokens + output_tokens + reasoning_tokens), 0) as avg_tokens,
            ROUND(AVG(tool_call_count), 1) as avg_tools,
            ROUND(AVG(api_call_count), 1) as avg_api_calls,
            ROUND(AVG(message_count), 0) as avg_messages
        FROM sessions 
        WHERE ended_at IS NOT NULL AND started_at IS NOT NULL
    """)
    aggregates = dict(c.fetchone())
    
    # Generation throughput per session (output + reasoning tokens/s)
    c.execute("""
        SELECT 
            ROUND(AVG((COALESCE(output_tokens, 0) + COALESCE(reasoning_tokens, 0)) * 1.0 / 
                 NULLIF(ended_at - started_at, 0)), 2) as avg_throughput
        FROM sessions 
        WHERE ended_at IS NOT NULL AND started_at IS NOT NULL 
          AND (ended_at - started_at) > 0
    """)
    row = c.fetchone()
    avg_throughput = row['avg_throughput'] or 0
    
    # Sessions per day (last 30 days)
    c.execute("""
        SELECT date(started_at, 'unixepoch') as day, COUNT(*) as count
        FROM sessions WHERE started_at IS NOT NULL
        GROUP BY day ORDER BY day DESC LIMIT 30
    """)
    sessions_per_day = [dict(r) for r in c.fetchall()][::-1]
    
    # Models in last 5 sessions
    c.execute("""
        SELECT model, COUNT(*) as count FROM sessions 
        WHERE model IS NOT NULL
        GROUP BY model ORDER BY COUNT(*) DESC
    """)
    model_usage = [dict(r) for r in c.fetchall()]
    
    return {
        'totalSessions': aggregates['total_sessions'] or 0,
        'avgDurationS': aggregates['avg_duration_s'] or 0,
        'avgTokens': aggregates['avg_tokens'] or 0,
        'avgTools': aggregates['avg_tools'] or 0,
        'avgApiCalls': aggregates['avg_api_calls'] or 0,
        'avgMessages': aggregates['avg_messages'] or 0,
        'avgThroughput': avg_throughput,
        'sessionsPerDay': sessions_per_day,
        'modelUsage': model_usage,
    }


def load_heatmap(conn):
    c = conn.cursor()
    c.execute("""
        SELECT s.model, tu.tool_name, COUNT(*) as total,
               SUM(CASE WHEN tu.success = 0 THEN 1 ELSE 0 END) as failures
        FROM tool_usage tu JOIN sessions s ON tu.session_id = s.id
        WHERE s.model IS NOT NULL AND tu.tool_name IS NOT NULL
        GROUP BY s.model, tu.tool_name HAVING total >= 3 ORDER BY failures DESC
    """)
    rows = c.fetchall()
    if not rows:
        return {'models': [], 'tools': [], 'matrix': []}
    model_set = []
    tool_set = []
    for r_ in rows:
        if r_['model'] not in model_set: model_set.append(r_['model'])
        if r_['tool_name'] not in tool_set: tool_set.append(r_['tool_name'])
    model_set = model_set[:6]
    tool_set = tool_set[:8]
    lookup = {(r_['model'], r_['tool_name']): r_['failures'] / r_['total'] for r_ in rows}
    heatmap_models = [m.split('/')[-1].split(':')[0][:15].upper() for m in model_set]
    return {
        'models': heatmap_models,
        'tools': tool_set,
        'matrix': [[round(lookup.get((m, t), 0), 3) for t in tool_set] for m in model_set],
    }


def load_openrouter(conn):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import os
    tz_name = os.environ.get("DASHBOARD_TIMEZONE", "Europe/Madrid")
    tz = ZoneInfo(tz_name)
    c = conn.cursor()
    c.execute("SELECT total_credits, total_usage, timestamp FROM account_snapshots ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    if not row:
        return {'totalCredits': 0, 'totalUsage': 0, 'today': 0, 'week': 0, 'month': 0}
    r = dict(row)
    total_credits = r['total_credits']
    total_usage = r['total_usage']

    # Calendar-aligned periods in Europe/Madrid
    now = datetime.now(tz)

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def spend_since(boundary_dt):
        """Find the snapshot closest to (but before) the boundary and diff with current."""
        ts = boundary_dt.timestamp()
        c2 = conn.cursor()
        c2.execute("""
            SELECT total_usage FROM account_snapshots
            WHERE timestamp <= ? ORDER BY timestamp DESC LIMIT 1
        """, (ts,))
        row2 = c2.fetchone()
        if row2:
            return round(max(total_usage - row2['total_usage'], 0), 2)
        # No snapshot before boundary = all activity is within the period
        return round(total_usage, 2)

    return {
        'totalCredits': round(total_credits, 2), 'totalUsage': round(total_usage, 2),
        'today': spend_since(day_start),
        'week': spend_since(week_start),
        'month': spend_since(month_start),
        'keyLimit': round(total_credits, 2),
    }


def load_system_health(conn):
    """Global system metrics: generation throughput, error rate, fallback rate, interruption rate."""
    c = conn.cursor()
    
    # Generation throughput global (output + reasoning tokens/s).
    c.execute("""
        SELECT 
            CASE WHEN SUM(ended_at - started_at) > 0 
                THEN ROUND(SUM(COALESCE(output_tokens, 0) + COALESCE(reasoning_tokens, 0)) * 1.0 / 
                     SUM(ended_at - started_at), 2)
                ELSE 0 
            END as global_throughput
        FROM sessions 
        WHERE ended_at IS NOT NULL AND started_at IS NOT NULL 
          AND (ended_at - started_at) > 0
    """)
    global_tp = dict(c.fetchone())['global_throughput'] or 0

    c.execute("""
        SELECT 
            MAX(ROUND((COALESCE(output_tokens, 0) + COALESCE(reasoning_tokens, 0)) * 1.0 / 
                (ended_at - started_at), 2)) as peak_throughput
        FROM sessions 
        WHERE ended_at IS NOT NULL AND started_at IS NOT NULL 
          AND (ended_at - started_at) > 0
    """)
    peak_tp = dict(c.fetchone())['peak_throughput'] or 0

    # Processing throughput keeps the old definition for diagnostics: input + output + reasoning.
    c.execute("""
        SELECT 
            CASE WHEN SUM(ended_at - started_at) > 0 
                THEN ROUND(SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0) + COALESCE(reasoning_tokens, 0)) * 1.0 / 
                     SUM(ended_at - started_at), 2)
                ELSE 0 
            END as global_processing_throughput,
            MAX(ROUND((COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0) + COALESCE(reasoning_tokens, 0)) * 1.0 / 
                (ended_at - started_at), 2)) as peak_processing_throughput
        FROM sessions 
        WHERE ended_at IS NOT NULL AND started_at IS NOT NULL 
          AND (ended_at - started_at) > 0
    """)
    processing_tp = dict(c.fetchone())
    
    # Error rate from errors_log (real system errors)
    c.execute("""SELECT COUNT(*) FROM errors_log""")
    total_errors = dict(c.fetchone())['COUNT(*)'] or 0
    c.execute("""SELECT COUNT(*) FROM sessions WHERE ended_at IS NOT NULL""")
    ended_sessions = dict(c.fetchone())['COUNT(*)'] or 1
    err_rate = round(total_errors / ended_sessions, 1)  # errors per session
    total_tc = ended_sessions  # reuse field name to avoid frontend break
    failures = total_errors
    
    # Fallback rate (from errors_log)
    c.execute("""
        SELECT COUNT(*) as fallbacks FROM errors_log 
        WHERE error_type LIKE '%fallback%' OR error_type LIKE '%primary%'
    """)
    fb = dict(c.fetchone())['fallbacks'] or 0
    c.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = dict(c.fetchone())['COUNT(*)'] or 1
    fb_rate = round(fb / total_sessions, 2)
    
    # Session interruption rate (user-initiated & system)
    c.execute("""
        SELECT 
            COUNT(*) as total_sessions,
            SUM(CASE WHEN end_reason = 'session_reset' OR end_reason IS NULL THEN 0 ELSE 1 END) as normal_end,
            SUM(CASE WHEN end_reason = 'session_reset' THEN 1 ELSE 0 END) as resets,
            SUM(CASE WHEN end_reason IS NULL THEN 1 ELSE 0 END) as active
        FROM sessions
    """)
    sr = dict(c.fetchone())
    ended = (sr['total_sessions'] or 0) - (sr['active'] or 0)
    reset_rate = round((sr['resets'] or 0) / max(ended, 1) * 100, 1)
    
    # Error count trend (last 30 days, from errors_log)
    c.execute("""
        SELECT date(timestamp, 'unixepoch') as day, COUNT(*) as total
        FROM errors_log WHERE timestamp IS NOT NULL
        GROUP BY day ORDER BY day DESC LIMIT 30
    """)
    err_trend = []
    for r in c.fetchall()[::-1]:
        rd = dict(r)
        err_trend.append({
            'date': rd['day'],
            'errorRate': round(rd['total'] / max(ended_sessions, 1), 1),
            'totalCalls': rd['total'],
            'failures': rd['total'],
        })
    
    return {
        'globalThroughput': global_tp,
        'peakThroughput': peak_tp,
        'globalProcessingThroughput': processing_tp['global_processing_throughput'] or 0,
        'peakProcessingThroughput': processing_tp['peak_processing_throughput'] or 0,
        'errorRate': err_rate,
        'totalToolCalls': total_tc,
        'failedToolCalls': failures,
        'fallbackCount': fb,
        'fallbackRate': fb_rate,
        'totalSessions': sr['total_sessions'] or 0,
        'sessionResetRate': reset_rate,
        'activeSessions': sr['active'] or 0,
        'errorRateTrend': err_trend,
    }


def load_collector(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM collector_runs ORDER BY started_at DESC LIMIT 1")
    row = c.fetchone()
    if not row:
        return {'cronId': u'—', 'lastRun': u'—', 'lastStatus': 'unknown', 'sessionsAdded': 0, 'nextRun': u'—'}
    r = dict(row)
    return {
        'cronId': 'on-demand', 'lastRun': fmt_date(r['ended_at'] or r['started_at']),
        'lastStatus': r['status'], 'sessionsAdded': r['sessions_added'] or 0,
        'nextRun': 'on dashboard start',
    }

def load_model_costs_real(conn):
    """Real cost per model using openrouter_daily_usage + today estimate from sessions."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import os
    tz_name = os.environ.get("DASHBOARD_TIMEZONE", "Europe/Madrid")
    tz = ZoneInfo(tz_name)
    
    c = conn.cursor()
    
    # 1) Get OR activity data (up to yesterday)
    c.execute("""
        SELECT model,
               SUM(usage) as real_cost,
               SUM(prompt_tokens) as input_tok,
               SUM(completion_tokens) as output_tok,
               SUM(requests) as reqs
        FROM openrouter_daily_usage
        GROUP BY model
    """)
    or_costs = {}
    for r in c.fetchall():
        or_costs[r['model']] = {
            'real_cost': r['real_cost'],
            'input_tok': r['input_tok'],
            'output_tok': r['output_tok'],
            'reqs': r['reqs'],
        }
    
    # 2) Get today's OR snapshot diff for total remaining
    c.execute("SELECT total_usage FROM account_snapshots ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    total_usage = latest['total_usage'] if latest else 0
    or_total = sum(v['real_cost'] for v in or_costs.values())
    
    # 3) Estimate today's costs per model using model_prices + today's session tokens
    today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    c.execute("""
        SELECT s.model,
               SUM(s.input_tokens) as in_tok,
               SUM(s.output_tokens) as out_tok,
               SUM(s.cache_read_tokens) as cache_tok
        FROM sessions s
        WHERE s.started_at >= ? AND s.model IS NOT NULL
        GROUP BY s.model
    """, (today_start,))
    today_sessions = {
        r['model']: {
            'in_tok': r['in_tok'],
            'out_tok': r['out_tok'],
            'cache_tok': r['cache_tok'],
        }
        for r in c.fetchall()
    }
    
    # Get model prices
    c.execute("SELECT model_id, input_price, output_price, cache_read_price FROM model_prices")
    prices = {}
    for r in c.fetchall():
        prices[r['model_id']] = r
    
    today_costs = {}
    for model, r in today_sessions.items():
        p = prices.get(model)
        if p:
            cost = (r['in_tok'] * (p['input_price'] or 0) +
                    r['out_tok'] * (p['output_price'] or 0) +
                    r['cache_tok'] * (p['cache_read_price'] or 0))
            today_costs[model] = round(cost, 4)
        else:
            today_costs[model] = 0.0
    
    # 4) Merge: OR data + today estimates, scale to match snapshot total
    # Get all models from sessions
    c.execute("SELECT DISTINCT model FROM sessions WHERE model IS NOT NULL ORDER BY model")
    all_models = [r['model'] for r in c.fetchall()]
    
    results = []
    for model in all_models:
        or_cost = or_costs.get(model, {}).get('real_cost', 0) or 0
        today_cost = today_costs.get(model, 0) or 0
        total_cost = or_cost + today_cost
        
        in_tok = (or_costs.get(model, {}).get('input_tok', 0) or 0) + (today_sessions.get(model, {}).get('in_tok', 0) or 0)
        out_tok = (or_costs.get(model, {}).get('output_tok', 0) or 0) + (today_sessions.get(model, {}).get('out_tok', 0) or 0)
        cache_tok = (today_sessions.get(model, {}).get('cache_tok', 0) or 0)
        reqs = (or_costs.get(model, {}).get('reqs', 0) or 0)
        
        results.append({
            'model': model,
            'input_tokens': in_tok,
            'output_tokens': out_tok,
            'cache_read_tokens': cache_tok,
            'reasoning_tokens': 0,
            'session_count': reqs,
            'real_cost': round(total_cost, 4),
        })
    
    return results



@app.route('/api/all')
def api_all():
    conn = get_db()
    try:
        models = load_models(conn)
        totals = load_totals(conn)
        today = datetime.now().date()
        days_since = max(totals.get('daysActive', 14), 7)
        tools_data = load_tools(conn)
        return jsonify({
            'models': models,
            'economicBreakdown': load_economic_breakdown(conn),
            'economicProviderUsage': load_economic_provider_usage(conn),
            'providerCatalog': get_provider_catalog(),
            'days': [(today - timedelta(days=i)).isoformat() for i in range(days_since - 1, -1, -1)],
            'tokensPerDay': load_tokens_per_day(conn, models),
            'tools': tools_data['tools'], 'toolDaily': tools_data['daily'],
            'toolTokenUsage': load_tool_token_usage(conn),
            'toolColors': TOOL_COLORS,
            'sources': load_sources(conn), 'recentSessions': load_recent_sessions(conn, 10),
            'errors': load_errors(conn), 'errorTrend': load_error_trend(conn),
            'heatmap': load_heatmap(conn), 'openRouter': load_openrouter(conn),
            'collector': load_collector(conn), 'totals': totals,
            'overviewExtras': load_overview_extras(conn),
            'sessionMetrics': load_sessions_analytics(conn),
            'systemHealth': load_system_health(conn),
            'modelCosts': load_model_costs_real(conn),
            'agentLog': load_agent_log_metrics(),
        })
    finally:
        conn.close()


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')



@app.route('/api/system')
def api_system():
    conn = get_db()
    try:
        return jsonify({
            'health': load_system_health(conn),
            'heatmap': load_heatmap(conn),
            'agentLog': load_agent_log_metrics(),
            'collector': load_collector(conn),
        })
    finally:
        conn.close()


@app.route('/api/sessions')
def api_sessions():
    conn = get_db()
    try:
        return jsonify(load_sessions_analytics(conn))
    finally:
        conn.close()

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


if __name__ == '__main__':
    run_collector()
    runtime = resolve_dashboard_runtime()
    print_startup_summary(runtime)
    app.run(host=runtime["host"], port=runtime["port"], debug=runtime["debug"])

"""Hermes Dashboard API — Flask backend serving real data from dashboard.db"""
import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')

# Register MIME types for JSX files (Babel standalone needs correct MIME)
import mimetypes
mimetypes.add_type('text/javascript', '.jsx')
mimetypes.add_type('text/javascript', '.mjs')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'dashboard.db')


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


MODEL_COLORS = [
    '#F59E0B', '#00D4B4', '#E84848', '#39D966', '#A855F7',
    '#EAB308', '#EC4899', '#F97316', '#06B6D4', '#84CC16',
]

TOOL_COLORS = [
    '#F59E0B', '#00D4B4', '#E84848', '#39D966', '#A855F7', '#EAB308',
    '#EC4899', '#F97316', '#06B6D4', '#84CC16', '#FBBF24', '#D946EF',
]


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
    return [{'name': dict(r)['tool_name'], 'count': dict(r)['count'],
             'success': dict(r)['success_rate'] / 100.0, 'durMs': dict(r)['avg_duration'],
             'color': TOOL_COLORS[i % len(TOOL_COLORS)]}
            for i, r in enumerate(c.fetchall())]


def load_sources(conn):
    c = conn.cursor()
    c.execute("SELECT source, COUNT(*) as count FROM sessions WHERE source IS NOT NULL GROUP BY source ORDER BY count DESC")
    source_colors = {'telegram': '#00D4B4', 'cli': '#F59E0B', 'api': '#A855F7'}
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
               SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as unresolved,
               COUNT(DISTINCT source) as source_count,
               MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
        FROM errors_log GROUP BY error_type ORDER BY total DESC LIMIT 20
    """)
    errors = []
    for row in c.fetchall():
        r = dict(row)
        priority = round(r['total'] * (1 + r['unresolved'] / max(r['total'], 1)), 1)
        c2 = conn.cursor()
        c2.execute("SELECT DISTINCT source FROM errors_log WHERE error_type = ? AND source IS NOT NULL LIMIT 5", (r['error_type'],))
        src_list = [row2['source'] for row2 in c2.fetchall()]
        errors.append({
            'pattern': r['error_type'], 'total': r['total'], 'unresolved': r['unresolved'],
            'sources': ','.join(src_list) if src_list else 'system',
            'firstSeen': fmt_date_short(r['first_seen']), 'lastSeen': fmt_date_short(r['last_seen']),
            'priority': priority,
        })
    return errors


def load_error_trend(conn):
    c = conn.cursor()
    c.execute("""
        SELECT date(timestamp, 'unixepoch') as day,
               CASE
                   WHEN error_type LIKE '%rate%limit%' OR error_type LIKE '%timeout%' OR error_type LIKE '%auth%' THEN 'api'
                   WHEN error_type LIKE '%tool%' OR error_type LIKE '%exec%' OR error_type LIKE '%shell%' THEN 'tool'
                   WHEN error_type LIKE '%empty%' OR error_type LIKE '%nudge%' OR error_type LIKE '%interrupt%' THEN 'agent'
                   WHEN error_type LIKE '%collector%' OR error_type LIKE '%db%' OR error_type LIKE '%lock%' THEN 'collector'
                   ELSE 'api'
               END as category, COUNT(*) as count
        FROM errors_log WHERE timestamp IS NOT NULL
        GROUP BY day, category ORDER BY day
    """)
    day_data = {}
    for row in c.fetchall():
        r = dict(row)
        day_data.setdefault(r['day'], {'api': 0, 'tool': 0, 'agent': 0, 'collector': 0})
        day_data[r['day']][r['category']] = r['count']
    return [{'date': d, **cats} for d, cats in sorted(day_data.items())]


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
    heatmap_models = [m.split('/')[-1].split(':')[0][:12].upper() for m in model_set]
    return {
        'models': heatmap_models,
        'tools': tool_set,
        'matrix': [[round(lookup.get((m, t), 0), 3) for t in tool_set] for m in model_set],
    }


def load_openrouter(conn):
    c = conn.cursor()
    c.execute("SELECT total_credits, total_usage, timestamp FROM account_snapshots ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    if not row:
        return {'totalCredits': 0, 'totalUsage': 0, 'today': 0, 'week': 0, 'month': 0}
    r = dict(row)
    total_credits = r['total_credits']
    total_usage = r['total_usage']
    now = time.time()

    def usage_since(ts):
        c2 = conn.cursor()
        c2.execute("SELECT total_usage FROM account_snapshots WHERE timestamp >= ? ORDER BY timestamp ASC LIMIT 1", (ts,))
        row2 = c2.fetchone()
        if row2: return round(total_usage - row2['total_usage'], 4)
        return round(total_usage * 0.1, 4)

    return {
        'totalCredits': round(total_credits, 2), 'totalUsage': round(total_usage, 2),
        'today': usage_since(now - 86400), 'week': usage_since(now - 7 * 86400),
        'month': usage_since(now - 30 * 86400), 'keyLimit': round(total_credits, 2),
    }


def load_collector(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM collector_runs ORDER BY started_at DESC LIMIT 1")
    row = c.fetchone()
    if not row:
        return {'cronId': u'—', 'lastRun': u'—', 'lastStatus': 'unknown', 'sessionsAdded': 0, 'nextRun': u'—'}
    r = dict(row)
    next_ts = (r['started_at'] or time.time()) + 3600
    return {
        'cronId': 'a4dcdae4dd65', 'lastRun': fmt_date(r['ended_at'] or r['started_at']),
        'lastStatus': r['status'], 'sessionsAdded': r['sessions_added'] or 0,
        'nextRun': fmt_date(next_ts),
    }


@app.route('/api/all')
def api_all():
    conn = get_db()
    try:
        models = load_models(conn)
        totals = load_totals(conn)
        today = datetime.now().date()
        days_since = max(totals.get('daysActive', 14), 7)
        return jsonify({
            'models': models,
            'days': [(today - timedelta(days=i)).isoformat() for i in range(days_since - 1, -1, -1)],
            'tokensPerDay': load_tokens_per_day(conn, models),
            'tools': load_tools(conn), 'toolColors': TOOL_COLORS,
            'sources': load_sources(conn), 'recentSessions': load_recent_sessions(conn, 10),
            'errors': load_errors(conn), 'errorTrend': load_error_trend(conn),
            'heatmap': load_heatmap(conn), 'openRouter': load_openrouter(conn),
            'collector': load_collector(conn), 'totals': totals,
        })
    finally:
        conn.close()


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


if __name__ == '__main__':
    print(f"🚀 Hermes Dashboard API + React on http://localhost:8502")
    app.run(host='0.0.0.0', port=8502, debug=True)

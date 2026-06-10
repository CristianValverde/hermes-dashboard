"""Agent log latency metrics for the dashboard."""

import os
import re
from collections import defaultdict


RESPONSE_READY_RE = re.compile(
    r"response ready:.*?time=([\d.]+)s api_calls=(\d+) response=(\d+) chars"
)


def _empty_metrics():
    return {
        "avgTime": 0,
        "medianTime": 0,
        "p95Time": 0,
        "avgApiCalls": 0,
        "totalResponses": 0,
        "trend": [],
        "audioCount": 0,
        "fallbackCount": 0,
    }


def _median(sorted_values):
    n = len(sorted_values)
    middle = n // 2
    if n % 2:
        return sorted_values[middle]
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def parse_agent_log_metrics(log_path):
    """Parse the full Hermes agent log for response latency metrics.

    The visible "avg response time" is intended to be a global response metric,
    so this scans the full file line-by-line instead of sampling the tail.
    """
    if not os.path.exists(log_path):
        return _empty_metrics()

    times = []
    calls = []
    chars = []
    daily_times = defaultdict(list)
    audio_count = 0
    fallback_count = 0
    warning_count = 0

    with open(log_path, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            match = RESPONSE_READY_RE.search(line)
            if match:
                response_time = float(match.group(1))
                times.append(response_time)
                calls.append(int(match.group(2)))
                chars.append(int(match.group(3)))

                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", line)
                if date_match:
                    daily_times[date_match.group(1)].append(response_time)

            if "Processing audio with duration" in line:
                audio_count += 1
            if "fallback" in line.lower():
                fallback_count += 1
            if "WARNING" in line:
                warning_count += 1

    if not times:
        return _empty_metrics()

    times_sorted = sorted(times)
    n = len(times_sorted)
    p95_index = min(int(n * 0.95), n - 1)

    trend = []
    for day in sorted(daily_times.keys())[-30:]:
        day_times = daily_times[day]
        trend.append({
            "date": day,
            "avgTime": round(sum(day_times) / len(day_times), 1),
            "count": len(day_times),
        })

    return {
        "avgTime": round(sum(times) / n, 1),
        "medianTime": round(_median(times_sorted), 1),
        "p95Time": round(times_sorted[p95_index], 1),
        "minTime": round(min(times), 1),
        "maxTime": round(max(times), 1),
        "avgApiCalls": round(sum(calls) / len(calls), 1),
        "avgChars": round(sum(chars) / len(chars), 0),
        "totalResponses": n,
        "trend": trend,
        "audioCount": audio_count,
        "fallbackCount": fallback_count,
        "warningCount": warning_count,
    }

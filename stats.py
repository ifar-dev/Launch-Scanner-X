"""
Running totals for alerts sent, persisted in state/stats.json (committed
back to the repo each run, same pattern as storage_json.py's seen.json).
"""

import json
import os
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_stats(path: str) -> dict:
    default = {
        "total_alerts": 0,
        "keyword_alerts": 0,
        "watch_alerts": 0,
        "since": _now_iso(),
        "last_updated": None,
    }
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return default

    for key, value in default.items():
        data.setdefault(key, value)
    return data


def record_run(path: str, keyword_alerts: int, watch_alerts: int):
    stats = load_stats(path)
    stats["keyword_alerts"] += keyword_alerts
    stats["watch_alerts"] += watch_alerts
    stats["total_alerts"] += keyword_alerts + watch_alerts
    stats["last_updated"] = _now_iso()

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(stats, f, indent=2)

    return stats

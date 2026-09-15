"""
Seen-tweet storage for the GitHub Actions variant.

GH Actions runners are thrown away after every run, so instead of a local
sqlite file (which would vanish each time), we keep a small JSON file of
recently-seen tweet IDs INSIDE the repo, and the workflow commits it back
after each run.

Each ID is stored with the UTC timestamp it was first seen. On save, we
keep only the MAX_STORED_IDS most recent entries, sorted explicitly by
timestamp -- this replaces an earlier, buggy version that stored IDs in a
plain set and sliced it by count. Python sets/dicts don't guarantee
insertion order is preserved through arbitrary operations, so that old
slice could silently drop recently-alerted IDs and cause duplicate
alerts. Sorting by the actual stored timestamp fixes that regardless of
any underlying collection ordering.
"""

import json
import os
from datetime import datetime, timezone

MAX_STORED_IDS = 1000


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_seen(path: str) -> dict:
    """Returns {tweet_id: iso_timestamp_first_seen}."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    seen_ids = data.get("seen_ids", {})

    # Migrate from the old list-based format if present, so existing
    # state files don't get wiped -- give migrated entries a fresh
    # timestamp (now) since we don't know their real first-seen time.
    if isinstance(seen_ids, list):
        ts = now_iso()
        return {tweet_id: ts for tweet_id in seen_ids}

    return seen_ids


def save_seen(path: str, seen_ids: dict):
    # Sort by timestamp (newest first) and keep only the most recent
    # MAX_STORED_IDS -- correct regardless of dict/insertion order, unlike
    # the old set-based slice.
    def _sort_key(item):
        tweet_id, ts_str = item
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)

    sorted_items = sorted(seen_ids.items(), key=_sort_key, reverse=True)
    trimmed = dict(sorted_items[:MAX_STORED_IDS])

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump({"seen_ids": trimmed}, f, indent=2)

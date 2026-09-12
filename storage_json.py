"""
Seen-tweet storage for the GitHub Actions variant.

GH Actions runners are thrown away after every run, so instead of a local
sqlite file (which would vanish each time), we keep a small JSON file of
recently-seen tweet IDs INSIDE the repo, and the workflow commits it back
after each run. Capped to the most recent N ids so the file doesn't grow
forever.
"""

import json
import os

MAX_STORED_IDS = 1000


def load_seen(path: str) -> set:
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return set(data.get("seen_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(path: str, seen_ids: set):
    # Keep only the most recent MAX_STORED_IDS (order isn't meaningful for a
    # set, but capping keeps the file small; good enough for dedup purposes).
    trimmed = list(seen_ids)[-MAX_STORED_IDS:]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump({"seen_ids": trimmed}, f, indent=2)

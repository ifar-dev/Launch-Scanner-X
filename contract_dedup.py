"""
Dedup by contract address (not tweet ID). Prevents alerting on the same
CA repeatedly when multiple different accounts tweet about the same
launch -- storage_json.py's seen.json only blocks re-alerting the exact
same TWEET, so five different posters mentioning the same CA would
otherwise all pass through as "new."

Stored in state/seen_contracts.json, same commit-back pattern as the
other state files.
"""

import json
import os
from datetime import datetime, timedelta, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_seen_contracts(path: str) -> dict:
    """Returns {contract_address: iso_timestamp_first_alerted}."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data.get("seen_contracts", {})


def save_seen_contracts(path: str, seen_contracts: dict, retention_hours: int):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=retention_hours)

    pruned = {}
    for contract, ts_str in seen_contracts.items():
        try:
            ts = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            pruned[contract] = ts_str
            continue
        if ts >= cutoff:
            pruned[contract] = ts_str

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump({"seen_contracts": pruned}, f, indent=2)


def already_alerted(seen_contracts: dict, contracts) -> bool:
    """contracts: iterable of contract address strings found in a tweet."""
    return any(c in seen_contracts for c in contracts)


def mark_alerted(seen_contracts: dict, contracts):
    ts = now_iso()
    for c in contracts:
        seen_contracts[c] = ts

"""
Meme/Token Launch Scanner -- GitHub Actions version
-------------------------------------------------------
Same detection logic as scanner.py, but runs ONCE per invocation instead
of looping forever -- GitHub Actions calls this on a cron schedule instead
of you keeping a process running. State (which tweets were already
alerted on) is kept in state/seen.json, which the workflow commits back
to the repo after each run.
"""

import logging
import os

import requests

import config
from signals import extract_signals, looks_like_launch
from storage_json import load_seen, save_seen

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("scanner_gh")

STATE_PATH = os.path.join(os.path.dirname(__file__), "state", "seen.json")

SEARCH_ENDPOINT = f"{config.TWITTERAPIS_BASE_URL}/tweet/advanced_search"


def build_search_query() -> str:
    terms = " OR ".join(f'"{t}"' for t in config.SEARCH_TERMS)
    return f"({terms}) -filter:replies -filter:retweets lang:en"


def fetch_tweets():
    """Page through TwitterAPIs.com advanced_search via cursor until we hit
    MAX_RESULTS_PER_POLL tweets (each page ~20 tweets = 1 billed call)."""
    headers = {"Authorization": f"Bearer {config.TWITTERAPIS_API_KEY}"}
    query = build_search_query()

    all_tweets = []
    cursor = None
    max_pages = max(1, -(-config.MAX_RESULTS_PER_POLL // 20))  # ceil division

    for _ in range(max_pages):
        params = {"query": query, "product": "Latest"}
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(SE

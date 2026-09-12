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

APIFY_RUN_URL = (
    "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={token}"
)


def build_search_query() -> str:
    terms = " OR ".join(f'"{t}"' for t in config.SEARCH_TERMS)
    return f"({terms}) -filter:replies -filter:retweets lang:en"


def fetch_tweets():
    payload = {
        "searchTerms": [build_search_query()],
        "maxItems": config.MAX_RESULTS_PER_POLL,
        "sort": "Latest",
    }
    url = APIFY_RUN_URL.format(actor=config.APIFY_ACTOR_ID, token=config.APIFY_API_TOKEN)
    resp = requests.post(url, json=payload, timeout=90)
    resp.raise_for_status()
    return resp.json()


def send_telegram_alert(text: str):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    if not resp.ok:
        log.error("Telegram send failed: %s", resp.text)


def format_alert(tweet: dict, cashtags, eth_addrs, sol_addrs) -> str:
    author = tweet.get("author", {}).get("userName") or tweet.get("author", {}).get("name", "unknown")
    text = tweet.get("text", "").strip()
    url = tweet.get("url") or tweet.get("twitterUrl", "")
    tags = ", ".join(f"${t.upper()}" for t in cashtags) if cashtags else "none"
    contracts = list(eth_addrs) + list(sol_addrs)
    contract_line = f"\nContract: <code>{contracts[0]}</code>" if contracts else ""
    return (
        f"🚨 <b>Possible launch spotted</b>\n"
        f"Ticker(s): <b>{tags}</b>{contract_line}\n"
        f"By: @{author}\n\n"
        f"{text[:400]}\n\n"
        f"{url}"
    )


def main():
    seen_ids = load_seen(STATE_PATH)

    try:
        tweets = fetch_tweets()
    except Exception as e:
        log.error("Fetch failed: %s", e)
        return

    new_alerts = 0
    for tweet in tweets:
        tweet_id = str(tweet.get("id") or tweet.get("tweetId") or tweet.get("url"))
        if not tweet_id or tweet_id in seen_ids:
            continue
        seen_ids.add(tweet_id)

        text = tweet.get("text", "")
        if not looks_like_launch(text):
            continue

        cashtags, eth_addrs, sol_addrs = extract_signals(text)
        if not cashtags and not eth_addrs and not sol_addrs:
            continue

        send_telegram_alert(format_alert(tweet, cashtags, eth_addrs, sol_addrs))
        new_alerts += 1

    save_seen(STATE_PATH, seen_ids)
    log.info("Run complete: %d new alert(s) sent, %d ids tracked", new_alerts, len(seen_ids))


if __name__ == "__main__":
    main()

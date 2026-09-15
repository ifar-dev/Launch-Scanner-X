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
from datetime import datetime, timezone

import requests

import config
from signals import extract_signals, looks_like_launch
from storage_json import load_seen, save_seen
from stats import record_run

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("scanner_gh")

STATE_PATH = os.path.join(os.path.dirname(__file__), "state", "seen.json")
STATS_PATH = os.path.join(os.path.dirname(__file__), "state", "stats.json")

SEARCH_ENDPOINT = f"{config.TWITTERAPIS_BASE_URL}/tweet/advanced_search"


def build_search_query() -> str:
    terms = " OR ".join(f'"{t}"' for t in config.SEARCH_TERMS)
    excludes = " ".join(f'-"{p}"' for p in config.EXCLUDE_PHRASES)
    return f"({terms}) {excludes} -filter:replies -filter:retweets lang:en".strip()


def build_watch_query():
    """Query matching original posts from any watched account. Returns None
    if no accounts are configured (feature disabled)."""
    if not config.WATCHED_ACCOUNTS:
        return None
    accounts = " OR ".join(f"from:{u}" for u in config.WATCHED_ACCOUNTS)
    return f"({accounts}) -filter:replies -filter:retweets"


def fetch_tweets(query: str):
    """Page through TwitterAPIs.com advanced_search via cursor until we hit
    MAX_RESULTS_PER_POLL tweets (each page ~20 tweets = 1 billed call)."""
    headers = {"Authorization": f"Bearer {config.TWITTERAPIS_API_KEY}"}

    all_tweets = []
    cursor = None
    max_pages = max(1, -(-config.MAX_RESULTS_PER_POLL // 20))  # ceil division

    for _ in range(max_pages):
        params = {"query": query, "product": "Latest"}
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(SEARCH_ENDPOINT, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        tweets = data.get("tweets", [])
        if not tweets:
            break
        all_tweets.extend(tweets)

        cursor = data.get("next_cursor")
        if not cursor:
            break

    return all_tweets


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


def _tweet_url(tweet: dict, author: str) -> str:
    tweet_id = tweet.get("id", "")
    return f"https://x.com/{author}/status/{tweet_id}" if author != "unknown" and tweet_id else ""


def format_alert(tweet: dict, cashtags, eth_addrs, sol_addrs) -> str:
    author_obj = tweet.get("author", {}) or {}
    author = author_obj.get("username", "unknown")
    text = tweet.get("text", "").strip()
    url = _tweet_url(tweet, author)
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


def format_watch_alert(tweet: dict, cashtags, eth_addrs, sol_addrs) -> str:
    author_obj = tweet.get("author", {}) or {}
    author = author_obj.get("username", "unknown")
    text = tweet.get("text", "").strip()
    url = _tweet_url(tweet, author)
    tags = ", ".join(f"${t.upper()}" for t in cashtags) if cashtags else "none"
    contracts = list(eth_addrs) + list(sol_addrs)
    contract_line = f"\nContract: <code>{contracts[0]}</code>" if contracts else ""
    return (
        f"📌 <b>Watched account posted a ticker</b>\n"
        f"Ticker(s): <b>{tags}</b>{contract_line}\n"
        f"By: @{author}\n\n"
        f"{text[:400]}\n\n"
        f"{url}"
    )


def is_excluded(text: str) -> bool:
    lowered = text.lower()
    return any(p.lower() in lowered for p in config.EXCLUDE_PHRASES)


def process_keyword_tweets(tweets, seen_ids) -> int:
    """Require ALL THREE: a launch-phrase match, a ticker, AND a contract
    address before alerting, excluding anything in EXCLUDE_PHRASES."""
    sent = 0
    for tweet in tweets:
        tweet_id = str(tweet.get("id") or tweet.get("tweetId") or tweet.get("url"))
        if not tweet_id or tweet_id in seen_ids:
            continue
        seen_ids[tweet_id] = datetime.now(timezone.utc).isoformat()

        text = tweet.get("text", "")
        if is_excluded(text):
            log.info("Excluded (matched EXCLUDE_PHRASES): %s", text[:100])
            continue
        if not looks_like_launch(text):
            continue

        cashtags, eth_addrs, sol_addrs = extract_signals(text)
        if not cashtags:
            continue
        if not eth_addrs and not sol_addrs:
            continue

        send_telegram_alert(format_alert(tweet, cashtags, eth_addrs, sol_addrs))
        sent += 1
    return sent


def process_watched_account_tweets(tweets, seen_ids) -> int:
    """Watched accounts: alert on ANY ticker/contract, no launch-phrase
    requirement -- the account itself is the signal."""
    sent = 0
    for tweet in tweets:
        tweet_id = str(tweet.get("id") or tweet.get("tweetId") or tweet.get("url"))
        if not tweet_id or tweet_id in seen_ids:
            continue
        seen_ids[tweet_id] = datetime.now(timezone.utc).isoformat()

        text = tweet.get("text", "")
        cashtags, eth_addrs, sol_addrs = extract_signals(text)
        if not cashtags and not eth_addrs and not sol_addrs:
            continue

        send_telegram_alert(format_watch_alert(tweet, cashtags, eth_addrs, sol_addrs))
        sent += 1
    return sent


def main():
    seen_ids = load_seen(STATE_PATH)
    keyword_sent = 0
    watch_sent = 0
    tweets_fetched_total = 0

    try:
        keyword_tweets = fetch_tweets(build_search_query())
        log.info("Fetched %d tweet(s) from keyword search", len(keyword_tweets))
        tweets_fetched_total += len(keyword_tweets)
        keyword_sent = process_keyword_tweets(keyword_tweets, seen_ids)
    except Exception as e:
        log.error("Keyword fetch failed: %s", e)

    watch_query = build_watch_query()
    if watch_query:
        try:
            watch_tweets = fetch_tweets(watch_query)
            log.info("Fetched %d tweet(s) from watched accounts", len(watch_tweets))
            tweets_fetched_total += len(watch_tweets)
            watch_sent = process_watched_account_tweets(watch_tweets, seen_ids)
        except Exception as e:
            log.error("Watched-account fetch failed: %s", e)

    save_seen(STATE_PATH, seen_ids)
    stats = record_run(STATS_PATH, keyword_sent, watch_sent, tweets_fetched_total)
    log.info(
        "Run complete: %d new alert(s) sent (%d ids tracked). Lifetime total: %d alerts (%d keyword, %d watched-account) from %d tweets fetched, since %s",
        keyword_sent + watch_sent,
        len(seen_ids),
        stats["total_alerts"],
        stats["keyword_alerts"],
        stats["watch_alerts"],
        stats["total_tweets_fetched"],
        stats["since"],
    )


if __name__ == "__main__":
    main()

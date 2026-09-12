"""
Configuration for the meme/token launch scanner.

Fill these in directly, OR set them as environment variables (recommended
so you don't accidentally commit secrets anywhere).
"""

import os

# --- Telegram ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

# --- Apify (X/Twitter data source) -------------------------------------
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN", "PUT_YOUR_APIFY_TOKEN_HERE")

# Cheapest pay-per-result tweet scraper actor as of testing.
# Double check current pricing/availability at https://apify.com/store before relying on it.
APIFY_ACTOR_ID = "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest"

# --- Search behavior -----------------------------------------------------
# Keywords/phrases to search for on X. Keep this focused -- broader terms
# mean more noise and more Apify credits spent per poll.
SEARCH_TERMS = [
    "new token launch",
    "fair launch",
    "stealth launch",
    "just launched $",
    "presale live",
    "contract address",
]

# How many results to pull per poll (higher = more Apify cost per run)
# Cost math: (86400 / POLL_INTERVAL_SECONDS) * MAX_RESULTS_PER_POLL * price_per_tweet
# At the settings below: ~5,760 reads/day -> roughly $0.58-1.44/day at
# $0.10-0.25 per 1,000 tweets. Raise MAX_RESULTS_PER_POLL or lower the
# interval only if you're missing launches -- both cost money linearly.
MAX_RESULTS_PER_POLL = 20

# How often to poll, in seconds. 5 minutes still catches a launch within
# its first few minutes while keeping Apify spend low. Each poll costs
# ~MAX_RESULTS_PER_POLL tweets worth of credits regardless of how many
# turn out to be new.
POLL_INTERVAL_SECONDS = 300

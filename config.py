"""
Configuration for the meme/token launch scanner.

Fill these in directly, OR set them as environment variables (recommended
so you don't accidentally commit secrets anywhere).
"""

import os

# --- Telegram ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

# --- TwitterAPIs.com (X/Twitter data source) ----------------------------
TWITTERAPIS_API_KEY = os.environ.get("TWITTERAPIS_API_KEY", "PUT_YOUR_TWITTERAPIS_KEY_HERE")
TWITTERAPIS_BASE_URL = "https://api.twitterapis.com/twitter"
# ~20 tweets per call at $0.0008/call. Verify current pricing at
# https://www.twitterapis.com/pricing before relying on it long-term.

# --- Search behavior -----------------------------------------------------
# Keywords/phrases to search for on X. Keep this focused -- broader terms
# mean more noise and more billed calls per poll.
SEARCH_TERMS = [
    "is live",
    "is now live",
    "is officially live",
]

# Phrases that should NEVER trigger an alert, even if they match a search
# term above. Case-insensitive substring match. Add anything here that's
# creating noise (e.g. a specific bot/account phrase you don't want).
EXCLUDE_PHRASES = [
    "moonshot push is live",
    "airdrop is live",
    "airdrop",
]

# --- Watched accounts -----------------------------------------------------
# X usernames (no @) to monitor directly. ANY original post from these
# accounts containing a $TICKER or contract address triggers an alert --
# no launch-phrase match required, since the source itself is the signal.
# Leave empty to disable this feature.
WATCHED_ACCOUNTS = [
    # "someaccount",
    # "anotheraccount",
]

# How many results to pull per poll. TwitterAPIs.com returns ~20 tweets
# per call regardless of this number -- set it to a multiple of 20 and the
# scanner will page (via cursor) to fetch that many, each page = 1 billed call.
# Cost math: (86400 / POLL_INTERVAL_SECONDS) * (MAX_RESULTS_PER_POLL / 20) * $0.0008
# At the settings below: ~96 polls/day * 1 call/poll * $0.0008 = ~$0.08/day.
MAX_RESULTS_PER_POLL = 20

# How often to poll, in seconds. 15 minutes cuts cost roughly 3x vs 5-min
# polling while still catching a launch well within its early window.
# Each poll costs at least one $0.0008 call regardless of how many
# results turn out to be new.
POLL_INTERVAL_SECONDS = 900

# How long (hours) to block a repeat alert for the SAME contract address,
# even when a different account posts about it. Without this, a trending
# CA gets re-alerted once per new poster, which feels like duplication.
CONTRACT_DEDUP_HOURS = 48

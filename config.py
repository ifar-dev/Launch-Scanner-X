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
# mean more noise and more Apify credits spent per poll.
SEARCH_TERMS = [
    "new token launch",
    "fair launch",
    "stealth launch",
    "just launched $",
    "presale live",
    "contract address",
]

# How many results to pull per poll. TwitterAPIs.com returns ~20 tweets
# per call regardless of this number -- set it to a multiple of 20 and the
# scanner will page (via cursor) to fetch that many, each page = 1 billed call.
# Cost math: (86400 / POLL_INTERVAL_SECONDS) * (MAX_RESULTS_PER_POLL / 20) * $0.0008
# At the settings below: ~288 polls/day * 1 call/poll * $0.0008 = ~$0.23/day.
MAX_RESULTS_PER_POLL = 20

# How often to poll, in seconds. 5 minutes still catches a launch within
# its first few minutes while keeping spend low. Each poll costs at least
# one $0.0008 call regardless of how many results turn out to be new.
POLL_INTERVAL_SECONDS = 300

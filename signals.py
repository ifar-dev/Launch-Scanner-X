"""Shared extraction/detection logic used by all scanner variants."""

import re

CASHTAG_RE = re.compile(r"\$([A-Za-z]{2,10})\b")
ETH_ADDR_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
SOL_ADDR_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

# TLDs that count as a "project domain" signal. Grouped for maintainability:
# - Core/general: the original curated set
# - Web3-native naming (ENS, Unstoppable Domains etc.)
# - Crypto/finance-flavored gTLDs
# - Broad set of tech/business gTLDs commonly used by crypto/SaaS projects
_PROJECT_TLDS = [
    # core / general
    "fun", "ai", "io", "gg", "xyz", "com", "net", "org", "app", "co", "so",
    "meme", "wtf", "lol", "finance", "money", "cash",
    # web3-native naming systems
    "eth", "crypto", "nft", "dao", "wallet", "bitcoin", "blockchain",
    # crypto/finance flavored
    "exchange", "trade", "markets", "capital", "fund", "ventures", "network",
    "tech", "dev", "digital", "community",
    # broad tech/business set
    "academy", "accountant", "agency", "art", "auto", "best", "bio", "blog",
    "camera", "chat", "cloud", "club", "codes", "coffee", "company",
    "computer", "design", "domains", "download", "estate", "expert", "farm",
    "games", "global", "guru", "health", "help", "host", "house", "icu",
    "info", "ink", "land", "life", "live", "market", "media", "news",
    "online", "party", "press", "pro", "pub", "realestate", "red", "rocks",
    "run", "services", "shop", "site", "social", "software", "space",
    "store", "studio", "support", "team", "today", "tools", "top", "travel",
    "video", "website", "wiki", "world",
]
PROJECT_DOMAIN_RE = re.compile(
    r"\b[a-zA-Z0-9-]+\.(?:" + "|".join(_PROJECT_TLDS) + r")\b",
    re.IGNORECASE,
)

LAUNCH_SIGNAL_WORDS = [
    "is live",
    "is now live",
    "is officially live",
]


def extract_signals(text: str):
    cashtags = set(CASHTAG_RE.findall(text))
    eth_addrs = set(ETH_ADDR_RE.findall(text))
    sol_addrs = set(m for m in SOL_ADDR_RE.findall(text) if len(m) >= 32)
    return cashtags, eth_addrs, sol_addrs


def looks_like_launch(text: str) -> bool:
    lowered = text.lower()
    return any(w in lowered for w in LAUNCH_SIGNAL_WORDS)


def has_project_domain(text: str) -> bool:
    """True if text mentions a project domain (pump.fun, heyaskr.ai, etc.)
    in a common crypto-launch or general tech/business TLD."""
    return bool(PROJECT_DOMAIN_RE.search(text))

"""Shared extraction/detection logic used by all scanner variants."""

import re

CASHTAG_RE = re.compile(r"\$([A-Za-z]{2,10})\b")
ETH_ADDR_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
SOL_ADDR_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
# Matches a project domain in common crypto-launch TLDs: pump.fun,
# heyaskr.ai, fairlaunch.gg, etc. Not exhaustive, but covers the TLDs
# these launch posts actually use.
PROJECT_DOMAIN_RE = re.compile(
    r"\b[a-zA-Z0-9-]+\.(?:fun|ai|io|gg|xyz|com|net|org|app|co|so|meme|wtf|lol|finance|money|cash)\b",
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
    in a common crypto-launch TLD."""
    return bool(PROJECT_DOMAIN_RE.search(text))

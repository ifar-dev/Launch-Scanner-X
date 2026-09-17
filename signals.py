"""Shared extraction/detection logic used by all scanner variants."""

import re

CASHTAG_RE = re.compile(r"\$([A-Za-z]{2,10})\b")
ETH_ADDR_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
SOL_ADDR_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
# Matches launchpad domains like pump.fun, believe.fun, faze.fun, etc.
FUN_DOMAIN_RE = re.compile(r"\b[a-zA-Z0-9-]+\.fun\b", re.IGNORECASE)

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


def has_fun_domain(text: str) -> bool:
    """True if text mentions a .fun launchpad domain (pump.fun, faze.fun, etc.)."""
    return bool(FUN_DOMAIN_RE.search(text))

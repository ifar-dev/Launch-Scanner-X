"""Shared extraction/detection logic used by all scanner variants."""

import re

CASHTAG_RE = re.compile(r"\$([A-Za-z]{2,10})\b")
ETH_ADDR_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
SOL_ADDR_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

LAUNCH_SIGNAL_WORDS = [
    "launch", "launching", "launched", "just deployed", "stealth launch",
    "fair launch", "presale", "new gem", "low cap", "just dropped",
    "ca:", "contract:", "going live", "just minted",
]


def extract_signals(text: str):
    cashtags = set(CASHTAG_RE.findall(text))
    eth_addrs = set(ETH_ADDR_RE.findall(text))
    sol_addrs = set(m for m in SOL_ADDR_RE.findall(text) if len(m) >= 32)
    return cashtags, eth_addrs, sol_addrs


def looks_like_launch(text: str) -> bool:
    lowered = text.lower()
    return any(w in lowered for w in LAUNCH_SIGNAL_WORDS)

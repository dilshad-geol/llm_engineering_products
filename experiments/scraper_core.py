"""
Lightweight HTML fetching helpers for text extraction from public web pages.

These utilities strip scripts/styles and return plain text suitable for LLM prompts.
Typical uses: summarization, brochure generation, and competitive intelligence briefs.

Author: Dilshad Raza
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

# Many sites reject requests without a browser-like User-Agent; this reduces 403s on blogs and docs sites.
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def fetch_website_contents(url: str, *, max_chars: int = 2_000, timeout: int = 25) -> str:
    """
    Download *url*, extract a readable text snapshot (title + body), and truncate.

    The character limit keeps downstream LLM calls predictable; raise *max_chars* when you
    need richer context (e.g. brochure assembly), or chunk text in your own pipeline.
    """
    response = requests.get(url, headers=_DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    if soup.body:
        # Drop noisy nodes so navigation chrome does not drown out real content.
        for tag in soup.body(["script", "style", "img", "input", "noscript"]):
            tag.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""

    combined = f"{title}\n\n{text}"
    return combined[:max_chars]


def fetch_website_links(url: str, timeout: int = 25) -> list[str]:
    """
    Return href values from anchor tags on *url*.

    Note: This parses the page a second time if you also call *fetch_website_contents*;
    for production you might cache the BeautifulSoup tree or combine both in one pass.
    """
    response = requests.get(url, headers=_DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    raw = [a.get("href") for a in soup.find_all("a")]
    # Filter Nones and empty strings while preserving order (duplicates may appear; the LLM can dedupe).
    return [h for h in raw if h]

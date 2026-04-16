"""
Executive web digest — turns any public URL into a short stakeholder-ready Markdown brief.

Use case: sales engineers and PMs skim vendor homepages, docs landing pages, or news posts
before a call. The model is instructed to ignore obvious navigation chrome and focus on claims,
products, and announcements.

Dependencies: OPENAI_API_KEY in environment (or .env via python-dotenv).

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Running as a script keeps imports local to this folder when executed from the repo root.
_TASKS_DIR = Path(__file__).resolve().parent
if str(_TASKS_DIR) not in sys.path:
    sys.path.insert(0, str(_TASKS_DIR))

from scraper_core import fetch_website_contents  # noqa: E402

# Model is configurable so you can swap faster/cheaper endpoints without editing code.
DEFAULT_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")

SYSTEM = """You are a concise business analyst.
You receive noisy text extracted from a web page (often with navigation labels mixed in).
Write a brief in Markdown with these sections:
- **Snapshot** — one tight paragraph on what this page is about.
- **Key offerings or themes** — bullets, only if supported by the text.
- **Notable updates** — bullets if the page mentions news, releases, or dates; otherwise say "None called out."
Ignore boilerplate navigation. Do not invent facts. If the excerpt is too thin, say what is missing.
Do not wrap your answer in a fenced code block; return Markdown only."""

USER_PREFIX = """Here is extracted text from a single web page. Summarize for a busy executive.

"""


def build_messages(page_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_PREFIX + page_text},
    ]


def digest_url(url: str, *, client: OpenAI, model: str) -> str:
    page_text = fetch_website_contents(url, max_chars=6_000)
    response = client.chat.completions.create(
        model=model,
        messages=build_messages(page_text),
        temperature=0.35,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Create an executive Markdown digest from a URL.")
    parser.add_argument("url", help="https://… page to fetch and summarize")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Chat model name (default env OPENAI_SUMMARY_MODEL or {DEFAULT_MODEL!r})",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY or add it to a .env file at your project root.")

    client = OpenAI()
    print(digest_url(args.url, client=client, model=args.model))


if __name__ == "__main__":
    main()

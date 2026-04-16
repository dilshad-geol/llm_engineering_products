"""
Release brief from a changelog page — distills shipping noise into a PM-facing summary.

Use case: weekly launch reviews, customer success newsletters, or sales enablement when the
canonical detail lives on a public changelog or release-notes URL.

Requires OPENAI_API_KEY.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_TASKS_DIR = Path(__file__).resolve().parent
if str(_TASKS_DIR) not in sys.path:
    sys.path.insert(0, str(_TASKS_DIR))

from scraper_core import fetch_website_contents  # noqa: E402

DEFAULT_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")

SYSTEM = """You are a product marketer. Given noisy HTML-extracted changelog text, produce Markdown:
- **Headline themes** (3 bullets max)
- **Customer-visible impact** (what users feel)
- **Risks or migrations** (if hinted)
- **Unknowns** if the excerpt is incomplete
Ignore navigation. No code fences."""


def brief(url: str, *, client: OpenAI, model: str) -> str:
    text = fetch_website_contents(url, max_chars=8_000)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Changelog excerpt:\n\n" + text},
        ],
        temperature=0.35,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Summarize a changelog/release-notes URL.")
    parser.add_argument("url")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(brief(args.url, client=client, model=args.model))


if __name__ == "__main__":
    main()

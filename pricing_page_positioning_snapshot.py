"""
Pricing page positioning snapshot — extracts plans, limits, and differentiators from a pricing URL.

Use case: competitive intel for sales engineers comparing contract structures without manually
transcribing tables from marketing sites.

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

SYSTEM = """You analyze SaaS pricing pages from raw text dumps.
Return Markdown with:
- **Plans** — name + price cues if present (use "not stated" when missing)
- **What scales** — seats, usage, API calls, etc., only if mentioned
- **Enterprise signals** — SSO, audit, SLA mentions
- **Gaps** — what a buyer would still need to ask sales
Do not invent numbers."""


def analyze_pricing(url: str, *, client: OpenAI, model: str) -> str:
    text = fetch_website_contents(url, max_chars=8_000)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Pricing page excerpt:\n\n" + text},
        ],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Summarize a /pricing style URL.")
    parser.add_argument("url")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(analyze_pricing(args.url, client=client, model=args.model))


if __name__ == "__main__":
    main()

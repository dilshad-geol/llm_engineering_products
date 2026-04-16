"""
Snarky web review — humorous Markdown riff on a page (tone experiment for social posts or newsletters).

Use case: content creators who want a fast, entertaining angle on a corporate site without
pretending the output is neutral analysis. Pair with `executive_web_digest_openai.py` when you
need sober and spicy variants from the same fetch pipeline.

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

DEFAULT_MODEL = os.getenv("OPENAI_SNARK_MODEL", "gpt-4o-mini")

SYSTEM = """You are a witty tech columnist. Roast gently: no slurs, no personal attacks on real humans.
Summarize what the site is trying to sell or say, poke fun at buzzwords, and still surface real facts.
Markdown output, no fenced wrapper around the whole answer."""


def review(url: str, *, client: OpenAI, model: str) -> str:
    text = fetch_website_contents(url, max_chars=5_000)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Page text:\n\n" + text},
        ],
        temperature=0.85,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Generate a snarky Markdown review of a URL.")
    parser.add_argument("url")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(review(args.url, client=client, model=args.model))


if __name__ == "__main__":
    main()

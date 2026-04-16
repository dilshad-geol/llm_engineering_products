"""
Documentation portal digest — first-pass orientation for a docs landing page.

Use case: developer relations or solutions architects skimming a vendor's docs hub before a
integration sprint; surfaces sections, quickstarts, and API references if the text reveals them.

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

SYSTEM = """You help engineers navigate documentation sites from noisy text.
Output Markdown:
- **Start here** — best entry points for a new integrator
- **Core concepts** — nouns that repeat (auth, webhooks, SDKs, quotas…)
- **Where to go next** — if the text lists sections, mirror them faithfully
Explicitly say if the excerpt looks like pure navigation with little content."""


def digest_docs_home(url: str, *, client: OpenAI, model: str) -> str:
    text = fetch_website_contents(url, max_chars=8_000)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Docs landing excerpt:\n\n" + text},
        ],
        temperature=0.25,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Digest a documentation portal landing URL.")
    parser.add_argument("url")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(digest_docs_home(args.url, client=client, model=args.model))


if __name__ == "__main__":
    main()

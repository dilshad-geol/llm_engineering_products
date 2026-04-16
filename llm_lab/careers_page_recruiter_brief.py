"""
Careers page talent snapshot — summarizes hiring signals from a company's jobs landing page.

Use case: recruiters building target account lists, or candidates deciding whether to invest time
in an application pipeline.

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

SYSTEM = """You advise talent teams. From messy careers-page text, output Markdown:
- **Hiring thesis** — what roles/domains they emphasize
- **Locations / remote** — only if stated
- **Stack hints** — technologies mentioned in job titles or blurbs
- **Process clues** — assessments, assignments, visa statements if any
If the page is thin, say so."""


def snapshot(url: str, *, client: OpenAI, model: str) -> str:
    text = fetch_website_contents(url, max_chars=7_000)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Careers page excerpt:\n\n" + text},
        ],
        temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Summarize a careers / jobs URL.")
    parser.add_argument("url")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(snapshot(args.url, client=client, model=args.model))


if __name__ == "__main__":
    main()

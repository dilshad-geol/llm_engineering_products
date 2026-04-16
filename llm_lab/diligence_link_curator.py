"""
Due-diligence link curator — turns a messy list of homepage anchors into a structured JSON shortlist.

Use case: M&A, partnership evaluation, or vendor reviews where analysts want "about, product,
security, team, careers" without clicking every footer link manually.

Requires OPENAI_API_KEY.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_TASKS_DIR = Path(__file__).resolve().parent
if str(_TASKS_DIR) not in sys.path:
    sys.path.insert(0, str(_TASKS_DIR))

from scraper_core import fetch_website_links  # noqa: E402

DEFAULT_MODEL = os.getenv("OPENAI_JSON_MODEL", "gpt-4o-mini")

SYSTEM = """
You help investors review a company website. Given a raw list of links from the homepage,
return JSON: {"links": [{"type": "...", "url": "https://..."}]}
Include items that inform risk and opportunity: about/company, product, pricing (if any),
security/trust, careers, press/news, docs, status page, social profiles.
Exclude mailto/tel, legal boilerplate-only pages when obvious, and duplicate URLs.
Resolve relative URLs using the provided base URL. Max 12 links.
""".strip()


def curate(url: str, *, client: OpenAI, model: str) -> dict:
    hrefs = fetch_website_links(url)
    user = f"Base URL: {url}\n\nRaw links:\n" + "\n".join(hrefs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content or "{}")


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Curate diligence links as JSON.")
    parser.add_argument("url")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(json.dumps(curate(args.url, client=client, model=args.model), indent=2))


if __name__ == "__main__":
    main()

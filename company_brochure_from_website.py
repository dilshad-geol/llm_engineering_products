"""
Company brochure generator — crawls a homepage, asks the model to pick useful follow-on links,
scrapes those pages, then drafts a Markdown brochure for customers, investors, and candidates.

This mirrors a common B2B pattern: combine cheap HTTP fetch + one structured LLM call + one
long-form generation call.

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

from scraper_core import fetch_website_contents, fetch_website_links  # noqa: E402

DEFAULT_MODEL = os.getenv("OPENAI_BROCHURE_MODEL", "gpt-4o-mini")

LINK_SYSTEM = """
You are given raw hyperlink targets extracted from a company's homepage.
Choose the URLs that best help a reader understand the company: about, product, careers,
docs, blog, news, social proof. Respond as JSON with this exact shape:
{"links": [{"type": "short label", "url": "https://..."}, ...]}
Rules:
- Resolve relative URLs against the site root provided in the user message.
- Exclude mailto:, tel:, privacy, terms, cookie banners, and pure asset links if identifiable.
- Cap the list at 8 items; prefer diversity (don't pick 5 identical blog permalinks unless necessary).
""".strip()

BROCHURE_SYSTEM = """
You are a marketing analyst. You receive noisy text from a company's landing page plus a few inner pages.
Write a concise brochure in Markdown (no fenced code blocks) suitable for prospects, investors, and recruits.
Sections: Overview, What they offer, Who they serve, Momentum or news (if any), Why it matters, Call to action.
Stay grounded in the text; flag uncertainty explicitly if the excerpts were thin.
""".strip()


def get_links_user_prompt(url: str) -> str:
    links = fetch_website_links(url)
    return (
        f"Homepage URL: {url}\n"
        "Pick the most useful follow-on links for a company brochure.\n"
        "Links (may include relative paths):\n\n" + "\n".join(links)
    )


def select_relevant_links(url: str, *, client: OpenAI, model: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": LINK_SYSTEM},
            {"role": "user", "content": get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


def assemble_multipage_context(home_url: str, link_payload: dict, *, max_chars_per_page: int) -> str:
    parts: list[str] = []
    parts.append("## Landing page\n\n")
    parts.append(fetch_website_contents(home_url, max_chars=max_chars_per_page))
    for item in link_payload.get("links", []):
        href = item.get("url")
        label = item.get("type", "link")
        if not href:
            continue
        parts.append(f"\n\n## Page: {label}\nURL: {href}\n\n")
        try:
            parts.append(fetch_website_contents(href, max_chars=max_chars_per_page))
        except Exception as exc:  # noqa: BLE001 — portfolio script: keep going on flaky pages
            parts.append(f"[Fetch skipped: {exc}]")
    return "".join(parts)


def create_brochure(company_name: str, home_url: str, *, client: OpenAI, model: str) -> str:
    links_json = select_relevant_links(home_url, client=client, model=model)
    context = assemble_multipage_context(home_url, links_json, max_chars_per_page=2_500)
    user = f"Company name (as given): {company_name}\nPrimary website: {home_url}\n\n{context}"
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.45,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Generate a Markdown brochure from a company website.")
    parser.add_argument("company_name", help='Display name e.g. "Acme Analytics"')
    parser.add_argument("home_url", help="Homepage URL")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(create_brochure(args.company_name, args.home_url, client=client, model=args.model))


if __name__ == "__main__":
    main()

"""
Side-by-side summary comparison: hosted OpenAI vs local Ollama on the same scraped page.

Use case: latency/cost tradeoffs, qualitative QA when swapping models, or demos for stakeholders
who want both "cloud quality" and "on-prem option" on identical input.

Author: Dilshad Raza
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

_TASKS_DIR = Path(__file__).resolve().parent
if str(_TASKS_DIR) not in sys.path:
    sys.path.insert(0, str(_TASKS_DIR))

from scraper_core import fetch_website_contents  # noqa: E402

PROMPT_SYSTEM = """You summarize web page text. Output 4 bullets max, plain text, no markdown.
Be factual; skip navigation fluff."""

USER_PREFIX = "Summarize this page excerpt:\n\n"


def run_openai(text: str, *, model: str) -> str:
    client = OpenAI()
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": USER_PREFIX + text},
        ],
        temperature=0.3,
    )
    return (r.choices[0].message.content or "").strip()


def run_ollama(text: str, *, base_url: str, model: str) -> str:
    client = OpenAI(base_url=base_url, api_key="ollama")
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": USER_PREFIX + text},
        ],
        temperature=0.3,
    )
    return (r.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <url>", file=sys.stderr)
        raise SystemExit(2)

    url = sys.argv[1]
    hosted_model = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    ollama_base = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1")

    text = fetch_website_contents(url, max_chars=4_000)

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required for hosted half of the comparison.")

    print("=== Hosted ===")
    print(run_openai(text, model=hosted_model))
    print("\n=== Local (Ollama) ===")
    print(run_ollama(text, base_url=ollama_base, model=ollama_model))


if __name__ == "__main__":
    main()

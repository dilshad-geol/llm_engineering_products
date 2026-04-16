"""
Local web digest — same pattern as a hosted summarizer, but calls a local Ollama OpenAI-compatible API.

Use case: air-gapped machines, zero recurring API cost, or prototyping on a laptop before
deploying to a hosted model.

Prerequisites: Ollama running (`ollama serve`) and a pulled model, e.g. `ollama pull llama3.2`.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI

_TASKS_DIR = Path(__file__).resolve().parent
if str(_TASKS_DIR) not in sys.path:
    sys.path.insert(0, str(_TASKS_DIR))

from scraper_core import fetch_website_contents  # noqa: E402

OLLAMA_BASE_URL = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

SYSTEM = """You summarize public web page text for a technical reader.
Respond in Markdown with: title line, 3–6 bullets of substance, and a **Caveats** line mentioning
if the excerpt looked like mostly navigation. Stay factual; do not fabricate product names."""

USER_PREFIX = "Page text follows. Summarize:\n\n"


def summarize_local(url: str, *, base_url: str, model: str) -> str:
    page_text = fetch_website_contents(url, max_chars=4_000)
    client = OpenAI(base_url=base_url, api_key="ollama")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_PREFIX + page_text},
        ],
        temperature=0.4,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a URL with a local Ollama model.")
    parser.add_argument("url", help="Page to fetch")
    parser.add_argument("--base-url", default=OLLAMA_BASE_URL, help="Ollama OpenAI-compatible base URL")
    parser.add_argument("--model", default=DEFAULT_OLLAMA_MODEL, help="Ollama model tag")
    args = parser.parse_args()
    print(summarize_local(args.url, base_url=args.base_url, model=args.model))


if __name__ == "__main__":
    main()

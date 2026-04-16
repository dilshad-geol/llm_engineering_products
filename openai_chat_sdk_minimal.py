"""
Minimal OpenAI Chat Completions example using the official Python SDK.

Use case: the smallest working reference when onboarding teammates or copying into a service.

Requires OPENAI_API_KEY.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Minimal chat completion via OpenAI SDK.")
    parser.add_argument("prompt", nargs="?", default="Explain what a REST endpoint is in two sentences.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MINIMAL_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    # `messages` is the chat transcript; even for one-shot questions you pass a single user turn.
    response = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        temperature=0.4,
    )
    print((response.choices[0].message.content or "").strip())


if __name__ == "__main__":
    main()

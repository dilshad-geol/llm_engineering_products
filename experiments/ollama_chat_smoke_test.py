"""
Ollama smoke test — verifies the local OpenAI-compatible endpoint answers a trivial prompt.

Use case: CI-style health checks for dev machines, or debugging firewall issues before heavier jobs.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os

from openai import OpenAI


def main() -> None:
    parser = argparse.ArgumentParser(description="Ping Ollama with a one-line prompt.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"),
        help="Ollama OpenAI-compatible base URL",
    )
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "llama3.2"))
    parser.add_argument("--prompt", default="Reply with exactly: pong")
    args = parser.parse_args()

    client = OpenAI(base_url=args.base_url, api_key="ollama")
    response = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        temperature=0,
    )
    print((response.choices[0].message.content or "").strip())


if __name__ == "__main__":
    main()

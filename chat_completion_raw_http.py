"""
Minimal Chat Completions call using raw HTTP (requests) instead of the OpenAI SDK.

Use case: debugging proxies, teaching how client libraries map to REST, or integrating with
languages/stacks where only HTTP is convenient.

Set OPENAI_API_KEY in the environment. The payload shape mirrors POST /v1/chat/completions.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv


def chat_completion_http(
    message: str,
    *,
    api_key: str,
    model: str = "gpt-4o-mini",
    endpoint: str = "https://api.openai.com/v1/chat/completions",
) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.2,
    }
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=60)
    response.raise_for_status()
    data = response.json()
    # The SDK hides this JSON shape; here we peel the assistant string explicitly.
    return data["choices"][0]["message"]["content"]


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Call OpenAI Chat Completions via HTTPS.")
    parser.add_argument("message", nargs="?", default="Say hello in one sentence.")
    parser.add_argument("--model", default=os.getenv("OPENAI_HTTP_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY missing.")

    try:
        print(chat_completion_http(args.message, api_key=key, model=args.model))
    except requests.HTTPError as exc:
        # Surface response body for 401/429 debugging without hiding the stack entirely.
        print(exc, file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text, file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

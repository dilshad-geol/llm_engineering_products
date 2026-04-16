"""
Email subject line assistant — suggests a single high-open-rate subject from draft body text.

Use case: outbound SDR sequences, newsletter sends, or support macros where the body is drafted
but the subject line is an afterthought.

Requires OPENAI_API_KEY (loaded from the environment or .env).

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

DEFAULT_MODEL = os.getenv("OPENAI_SUBJECT_MODEL", "gpt-4o-mini")

SYSTEM = """You write email subject lines.
Rules:
- Output exactly one subject line, no quotes, no preamble, no bullet points.
- Prefer specificity over hype; avoid ALL CAPS and spammy words unless the body justifies it.
- If the body is empty or useless, output: Needs a real email body"""


def suggest_subject(body: str, *, client: OpenAI, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": body.strip()},
        ],
        temperature=0.7,
    )
    return (response.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Suggest one subject line from email body text.")
    parser.add_argument(
        "--body-file",
        help="Path to a text file containing the email body (stdin used if omitted)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required.")

    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        import sys as _sys

        body = _sys.stdin.read()

    client = OpenAI()
    print(suggest_subject(body, client=client, model=args.model))


if __name__ == "__main__":
    main()

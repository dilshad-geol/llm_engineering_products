"""
Structured support triage — classifies a customer message into JSON routing metadata.

Use case: CRM automation (route to L2, billing, or success), SLA tagging, or prepopulating
macros before a human reads the thread.

Requires OPENAI_API_KEY.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENAI_TRIAGE_MODEL", "gpt-4o-mini")

SYSTEM = """
You are a support routing model. Read the customer's message and respond ONLY with JSON:
{
  "intent": "billing|bug|how_to|account|feedback|other",
  "urgency": "low|medium|high",
  "one_line_summary": "10-20 words",
  "suggested_team": "billing|engineering|success|sales|unknown",
  "customer_sentiment": "calm|frustrated|angry|excited|unknown"
}
If information is missing, choose the closest label and mention ambiguity in one_line_summary.
""".strip()


def triage(message: str, *, client: OpenAI, model: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": message.strip()},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    return json.loads(response.choices[0].message.content or "{}")


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Triage a support message to JSON.")
    parser.add_argument("--message-file", help="UTF-8 file with the customer message")
    parser.add_argument("--message", default="", help="Inline message")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if args.message_file:
        from pathlib import Path

        text = Path(args.message_file).read_text(encoding="utf-8")
    else:
        text = args.message

    if not text.strip():
        raise SystemExit("Provide --message or --message-file.")

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    print(json.dumps(triage(text, client=client, model=args.model), indent=2))


if __name__ == "__main__":
    main()

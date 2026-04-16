#!/usr/bin/env python3
"""
Run a short roundtable where three models (OpenAI, Anthropic, Google Gemini)
each speak in turn from a shared transcript. Useful for comparing tone,
reasoning style, and agreement on a single topic.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI


def _require_keys() -> tuple[str | None, str | None, str | None]:
    load_dotenv(override=True)
    o = os.getenv("OPENAI_API_KEY")
    a = os.getenv("ANTHROPIC_API_KEY")
    g = os.getenv("GOOGLE_API_KEY")
    missing = []
    if not o:
        missing.append("OPENAI_API_KEY")
    if not a:
        missing.append("ANTHROPIC_API_KEY")
    if not g:
        missing.append("GOOGLE_API_KEY")
    if missing:
        print("Set these environment variables (e.g. in a .env file): " + ", ".join(missing), file=sys.stderr)
        sys.exit(1)
    return o, a, g


def _clients() -> tuple[OpenAI, OpenAI, OpenAI]:
    _, anthropic_key, google_key = _require_keys()
    openai = OpenAI()
    anthropic = OpenAI(api_key=anthropic_key, base_url="https://api.anthropic.com/v1/")
    gemini = OpenAI(
        api_key=google_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    return openai, anthropic, gemini


def conversation_text(history: list[tuple[str, str]]) -> str:
    return "\n".join(f"{speaker}: {message}" for speaker, message in history)


def call_speaker(
    name: str,
    history: list[tuple[str, str]],
    participants: dict,
) -> str:
    config = participants[name]
    system_prompt: str = config["system"]
    user_prompt = f"""
You are {name} in a conversation with Alex, Blake, and Charlie.
Here is the full conversation so far:

{conversation_text(history)}

Now respond as {name} with your next message in 1-2 sentences.
""".strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    client: OpenAI = config["client"]
    response = client.chat.completions.create(model=config["model"], messages=messages)
    return response.choices[0].message.content or ""


def build_participants(openai: OpenAI, anthropic: OpenAI, gemini: OpenAI) -> dict:
    return {
        "Alex": {
            "client": openai,
            "model": "gpt-4.1-mini",
            "system": (
                "You are Alex. You are sharp, skeptical, and argumentative, "
                "but stay constructive and non-abusive."
            ),
        },
        "Blake": {
            "client": anthropic,
            "model": "claude-haiku-4-5",
            "system": "You are Blake. You are calm, collaborative, and try to find common ground.",
        },
        "Charlie": {
            "client": gemini,
            "model": "gemini-2.5-flash-lite",
            "system": "You are Charlie. You are curious and analytical, and you ask clarifying questions.",
        },
    }


def run_roundtable(
    topic: str,
    extra_rounds: int,
    printer: Callable[[str, str], None] | None = None,
) -> list[tuple[str, str]]:
    openai, anthropic, gemini = _clients()
    participants = build_participants(openai, anthropic, gemini)

    conversation: list[tuple[str, str]] = [
        ("Alex", f"Let's discuss this: {topic}"),
        ("Blake", "I'll start by noting context and tradeoffs matter as much as the headline answer."),
        ("Charlie", "Before we commit, what criteria should we use to judge a good outcome?"),
    ]

    def _print(speaker: str, text: str) -> None:
        if printer:
            printer(speaker, text)
        else:
            print(f"\n[{speaker}]\n{text}\n")

    for speaker, message in conversation:
        _print(speaker, message)

    order = ["Alex", "Blake", "Charlie"]
    for _ in range(extra_rounds):
        for speaker in order:
            next_message = call_speaker(speaker, conversation, participants)
            conversation.append((speaker, next_message))
            _print(speaker, next_message)

    return conversation


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-model panel discussion runner")
    parser.add_argument(
        "--topic",
        default="Whether remote work is better than office work for most knowledge teams.",
        help="Opening topic for the panel",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=2,
        help="How many full cycles (Alex, Blake, Charlie each speak once per cycle) after the opening lines",
    )
    args = parser.parse_args()
    if args.rounds < 0:
        print("--rounds must be >= 0", file=sys.stderr)
        sys.exit(1)
    run_roundtable(args.topic, args.rounds)


if __name__ == "__main__":
    main()

"""
Multi-turn chat with explicit history — demonstrates stateless LLM calls with full message replay.

Use case: any production chat UI must append prior turns to `messages` because the model has
no persistence; this script is a minimal REPL you can extend with persistence, RAG, or tool calls.

Requires OPENAI_API_KEY.

Author: Dilshad Raza
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

SYSTEM = """You are a helpful assistant. Keep answers short unless the user asks for depth."""


def run_turn(client: OpenAI, history: list[dict], user_line: str, *, model: str) -> tuple[list[dict], str]:
    # Mutate a fresh list so callers can keep an immutable snapshot if they want.
    messages = [*history, {"role": "user", "content": user_line}]
    response = client.chat.completions.create(model=model, messages=messages, temperature=0.5)
    assistant = (response.choices[0].message.content or "").strip()
    # Critical: store the assistant reply so the *next* call can replay full context.
    messages.append({"role": "assistant", "content": assistant})
    return messages, assistant


def main() -> None:
    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required.")

    client = OpenAI()
    # Seed with the system message once; some teams inject it every request — either works if consistent.
    history: list[dict] = [{"role": "system", "content": SYSTEM}]

    print("Chat REPL. Empty line exits. This is stateless: history grows client-side.\n")
    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            break
        history, reply = run_turn(client, history, line, model=DEFAULT_MODEL)
        print(f"Model: {reply}\n")


if __name__ == "__main__":
    main()

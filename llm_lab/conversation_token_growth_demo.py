"""
Conversation token growth demo — prints how token counts climb as you append turns.

Use case: explains why long chats cost more and why summarization or truncation strategies matter.

This script does not call any LLM; it only measures tiktoken length for educational output.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse

import tiktoken


def encode_messages(messages: list[dict], encoding_name: str) -> int:
    """
    Approximate token usage for a flat list of chat dicts.

    Note: Real providers add per-message overhead and special tokens; this is a teaching estimate.
    """
    enc = tiktoken.get_encoding(encoding_name)
    blob = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    return len(enc.encode(blob))


def main() -> None:
    parser = argparse.ArgumentParser(description="Show token growth as chat history lengthens.")
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--turns", type=int, default=6, help="How many user/assistant pairs to simulate")
    args = parser.parse_args()

    system = {"role": "system", "content": "You are a concise assistant."}
    history = [system]

    for i in range(args.turns):
        history.append({"role": "user", "content": f"Question {i}: what is {i} squared?"})
        history.append({"role": "assistant", "content": f"Answer {i}: {i * i}."})
        n = encode_messages(history, args.encoding)
        print(f"After turn {i + 1}: ~{n} tokens (tiktoken estimate on concatenated roles)")


if __name__ == "__main__":
    main()

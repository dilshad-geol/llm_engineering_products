"""
Technical explainer — answers engineering questions with either OpenAI or Ollama.

Use case: on-call runbooks, internal Stack Overflow bots, or interview-prep helpers where some
users need cloud quality and others need a fully local path.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI

SYSTEM = """You are a patient senior software engineer.
When the user pastes code or asks how something works:
- Start with one-sentence gist.
- Explain mechanics and edge cases (None, empty collections, exceptions).
- Use Markdown with short headings; tiny code fences only when clarifying.
Avoid filler."""


def explain_openai(question: str, *, model: str) -> str:
    client = OpenAI()
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question.strip()},
        ],
        temperature=0.35,
    )
    return (r.choices[0].message.content or "").strip()


def explain_ollama(question: str, *, base_url: str, model: str) -> str:
    client = OpenAI(base_url=base_url, api_key="ollama")
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question.strip()},
        ],
        temperature=0.35,
    )
    return (r.choices[0].message.content or "").strip()


def main() -> None:
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="Explain a technical question with OpenAI or Ollama.")
    parser.add_argument("--backend", choices=("openai", "ollama"), default="openai")
    parser.add_argument(
        "--question-file",
        help="UTF-8 file with your question (otherwise use --question)",
    )
    parser.add_argument("--question", default="", help="Inline question text")
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_EXPLAIN_MODEL", "gpt-4o-mini"))
    parser.add_argument("--ollama-model", default=os.getenv("OLLAMA_MODEL", "llama3.2"))
    parser.add_argument("--ollama-base-url", default=os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"))
    args = parser.parse_args()

    if args.question_file:
        from pathlib import Path

        q = Path(args.question_file).read_text(encoding="utf-8")
    else:
        q = args.question

    if not q.strip():
        raise SystemExit("Provide --question or --question-file.")

    if args.backend == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY required for OpenAI backend.")
        print(explain_openai(q, model=args.openai_model))
    else:
        print(explain_ollama(q, base_url=args.ollama_base_url, model=args.ollama_model))


if __name__ == "__main__":
    main()

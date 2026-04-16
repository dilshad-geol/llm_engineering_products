"""
Token budget estimator — counts tokens with tiktoken and estimates rough USD cost.

Use case: guardrails before sending huge RAG payloads, pricing internal tools, or teaching
why "memory" in chat apps is just re-sent context (longer history ⇒ more tokens).

Pricing below is *illustrative* — replace rates with your org's actual list prices.

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import tiktoken

# Placeholder dollars per 1M tokens; adjust to match your provider and model.
# Keeping them as constants makes the arithmetic obvious in portfolio reviews.
DEFAULT_INPUT_PER_MILLION = float(os.getenv("ILLUSTRATIVE_INPUT_USD_PER_MTOK", "0.15"))
DEFAULT_OUTPUT_PER_MILLION = float(os.getenv("ILLUSTRATIVE_OUTPUT_USD_PER_MTOK", "0.60"))


def count_tokens(text: str, encoding_name: str) -> int:
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))


def estimate_cost(
    prompt_tokens: int,
    *,
    expected_output_tokens: int,
    input_per_million: float,
    output_per_million: float,
) -> tuple[float, float]:
    """Return (input_cost, output_cost) in USD for the illustrative rates."""
    in_cost = (prompt_tokens / 1_000_000) * input_per_million
    out_cost = (expected_output_tokens / 1_000_000) * output_per_million
    return in_cost, out_cost


def main() -> None:
    parser = argparse.ArgumentParser(description="Token count + rough cost estimate.")
    parser.add_argument(
        "--text-file",
        help="UTF-8 file to measure; if omitted, a short demo string is used",
    )
    parser.add_argument(
        "--encoding",
        default="cl100k_base",
        help="tiktoken encoding name (cl100k_base matches many OpenAI chat models)",
    )
    parser.add_argument(
        "--expect-output-tokens",
        type=int,
        default=400,
        help="Hypothetical completion length for a rough total cost band",
    )
    args = parser.parse_args()

    text = (
        Path(args.text_file).read_text(encoding="utf-8")
        if args.text_file
        else "Hi — this is a demo string for token counting. " * 20
    )
    n = count_tokens(text, args.encoding)
    in_usd, out_usd = estimate_cost(
        n,
        expected_output_tokens=args.expect_output_tokens,
        input_per_million=DEFAULT_INPUT_PER_MILLION,
        output_per_million=DEFAULT_OUTPUT_PER_MILLION,
    )

    print(f"Encoding: {args.encoding}")
    print(f"Characters: {len(text)}")
    print(f"Tokens: {n}")
    print(
        f"Illustrative cost (input ${DEFAULT_INPUT_PER_MILLION}/MTok, "
        f"output ${DEFAULT_OUTPUT_PER_MILLION}/MTok, {args.expect_output_tokens} out tok): "
        f"${in_usd + out_usd:.6f} (in ${in_usd:.6f} + out ${out_usd:.6f})"
    )


if __name__ == "__main__":
    main()

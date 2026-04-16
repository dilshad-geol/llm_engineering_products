#!/usr/bin/env python3
"""
FlightAI Virtual Agent
----------------------
Customer support assistant for FlightAI: multi-model inference, streaming replies, and live
fare lookup through a managed tool (inventory-backed pricing).

• **Model routing** — switch between OpenAI, Anthropic, or Google Gemini using OpenAI-compatible
  HTTP clients (single integration surface for ops).
• **Streaming** — token streaming for low-latency chat in the web console.
• **Agent tools** — function calling with automatic follow-up turns until the model returns a
  final natural-language answer.

CLI
~~~
  uv run python task2/advanced_portfolio_assistant.py self-test
      Run a quick console self-test (connectivity, streaming sample, fare tool path).
      (``demo`` is accepted as an alias.)

  uv run python task2/advanced_portfolio_assistant.py serve
      Start the FlightAI support console in the browser (Gradio).
      (``ui`` is accepted as an alias.)

Configuration
~~~~~~~~~~~~~
  OPENAI_API_KEY — required for fare lookup and full self-test
  ANTHROPIC_API_KEY, GOOGLE_API_KEY — optional alternate backends
  OPENAI_MODEL, ANTHROPIC_MODEL, GEMINI_MODEL — model overrides

Author: Dilshad Raza
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import threading
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

PRODUCT_NAME = "FlightAI Virtual Agent"


def _load_env() -> None:
    """Load environment from `.env` when the process can read it."""
    try:
        load_dotenv(override=True)
    except (OSError, PermissionError):
        pass


# ---------------------------------------------------------------------------
# Fare inventory (in-memory store; swap for your reservation API)
# ---------------------------------------------------------------------------

_DB_LOCK = threading.Lock()
_DB_CONN: sqlite3.Connection | None = None


def _connection() -> sqlite3.Connection:
    """Thread-safe connection to the in-memory fare table used by the pricing tool."""
    global _DB_CONN
    with _DB_LOCK:
        if _DB_CONN is None:
            _DB_CONN = sqlite3.connect(":memory:", check_same_thread=False)
            _DB_CONN.execute(
                "CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL NOT NULL)"
            )
            seed = [
                ("london", 799.0),
                ("paris", 899.0),
                ("tokyo", 1400.0),
                ("berlin", 499.0),
            ]
            _DB_CONN.executemany(
                "INSERT OR REPLACE INTO prices (city, price) VALUES (?, ?)", seed
            )
            _DB_CONN.commit()
        return _DB_CONN


def get_ticket_price(destination_city: str) -> str:
    """Return the published return fare for a destination from FlightAI inventory."""
    city = destination_city.strip().lower()
    conn = _connection()
    cur = conn.execute("SELECT price FROM prices WHERE city = ?", (city,))
    row = cur.fetchone()
    if row is None:
        return (
            f"No published fare for {destination_city!r}. "
            "Available cities: London, Paris, Tokyo, Berlin."
        )
    return f"Return fare to {destination_city.title()}: ${row[0]:.0f} USD (FlightAI published rate)."


PRICE_TOOL_DEF: dict[str, Any] = {
    "name": "get_ticket_price",
    "description": "Look up the current published return fare to a destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "Destination city name, e.g. Paris",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False,
    },
}

TOOLS: list[dict[str, Any]] = [{"type": "function", "function": PRICE_TOOL_DEF}]


# ---------------------------------------------------------------------------
# Model providers (unified OpenAI-compatible client configuration)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Provider:
    key: str
    label: str
    base_url: str | None
    env_api_var: str
    default_model: str


def _providers() -> list[Provider]:
    return [
        Provider(
            key="openai",
            label="OpenAI",
            base_url=None,
            env_api_var="OPENAI_API_KEY",
            default_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ),
        Provider(
            key="anthropic",
            label="Anthropic (OpenAI-compatible)",
            base_url="https://api.anthropic.com/v1/",
            env_api_var="ANTHROPIC_API_KEY",
            default_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        ),
        Provider(
            key="gemini",
            label="Gemini (OpenAI-compatible)",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            env_api_var="GOOGLE_API_KEY",
            default_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        ),
    ]


def make_client(provider: Provider) -> OpenAI | None:
    key = os.getenv(provider.env_api_var)
    if not key:
        return None
    if provider.base_url is None:
        return OpenAI(api_key=key)
    return OpenAI(api_key=key, base_url=provider.base_url)


SYSTEM_FLIGHT = """You are FlightAI customer support: concise, polite, at most ~2 sentences unless the user asks for more.
When the customer asks for a price, use the fare lookup tool. Never invent fares."""


def normalize_history(history: list) -> list[dict[str, str]]:
    """Normalize Gradio chat history into role/content messages."""
    return [{"role": h["role"], "content": h["content"]} for h in history]


def handle_tool_calls(message: Any) -> list[dict[str, Any]]:
    """Run every tool call requested in a single assistant turn."""
    out: list[dict[str, Any]] = []
    for call in message.tool_calls or []:
        if call.function.name == "get_ticket_price":
            args = json.loads(call.function.arguments or "{}")
            city = args.get("destination_city", "")
            result = get_ticket_price(str(city))
            out.append(
                {"role": "tool", "content": result, "tool_call_id": call.id}
            )
    return out


def complete_with_tools(
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
) -> str:
    """
    Resolve all tool calls in a loop until the model produces a final user-facing message.

    Supports chained lookups (e.g. multiple cities or follow-up after inventory results).
    """
    response = client.chat.completions.create(
        model=model, messages=messages, tools=TOOLS, tool_choice="auto"
    )
    while response.choices[0].finish_reason == "tool_calls":
        assistant_msg = response.choices[0].message
        messages.append(
            {
                "role": "assistant",
                "content": assistant_msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (assistant_msg.tool_calls or [])
                ],
            }
        )
        messages.extend(handle_tool_calls(assistant_msg))
        response = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, tool_choice="auto"
        )
    return (response.choices[0].message.content or "").strip()


def stream_chat(
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
    *,
    use_tools: bool,
) -> Generator[str, None, None]:
    """Stream assistant text; when tools are enabled, returns one final string after tool resolution."""
    if use_tools:
        text = complete_with_tools(client, model, list(messages))
        yield text
        return

    stream = client.chat.completions.create(
        model=model, messages=messages, stream=True, temperature=0.4
    )
    buf = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        buf += delta
        yield buf


# ---------------------------------------------------------------------------
# Console self-test (no browser)
# ---------------------------------------------------------------------------


def run_self_test() -> None:
    _load_env()
    _connection()

    print(f"{PRODUCT_NAME} — self-test\n")
    print("Model backends")
    for p in _providers():
        ok = bool(os.getenv(p.env_api_var))
        print(f"  • {p.label}: {'configured' if ok else f'not set ({p.env_api_var})'}")

    openai_p = next(x for x in _providers() if x.key == "openai")
    oa_client = make_client(openai_p)
    if oa_client:
        print("\nStreaming (sample)")
        msgs = [
            {"role": "system", "content": "You reply in at most 12 words."},
            {"role": "user", "content": "Why use streaming for chat UIs?"},
        ]
        final = ""
        for partial in stream_chat(oa_client, openai_p.default_model, msgs, use_tools=False):
            final = partial
        print(f"  {final}")

        print("\nFare lookup (agent tool)")
        msgs2 = [
            {"role": "system", "content": SYSTEM_FLIGHT},
            {
                "role": "user",
                "content": "How much is a return ticket to Paris on FlightAI?",
            },
        ]
        answer = complete_with_tools(oa_client, openai_p.default_model, msgs2)
        print(f"  {answer}")
    else:
        print("\nOpenAI not configured — set OPENAI_API_KEY for streaming and fare tool checks.")

    print("\nAlternate backends (plain chat smoke test)")
    probe = (
        "In one sentence, name a benefit of standardizing on an OpenAI-compatible HTTP API "
        "for multiple model vendors."
    )
    for p in _providers():
        if p.key == "openai":
            continue
        c = make_client(p)
        if not c:
            print(f"  • {p.label}: not configured")
            continue
        try:
            r = c.chat.completions.create(
                model=p.default_model,
                messages=[{"role": "user", "content": probe}],
                temperature=0.3,
            )
            text = (r.choices[0].message.content or "").strip()
            print(f"  • {p.label}: {text}")
        except Exception as exc:  # noqa: BLE001
            print(f"  • {p.label}: unavailable ({exc})")


# ---------------------------------------------------------------------------
# Web console (Gradio)
# ---------------------------------------------------------------------------


def launch_console() -> None:
    import gradio as gr

    _load_env()
    _connection()

    provider_keys = [p.key for p in _providers()]
    provider_labels = {p.key: p.label for p in _providers()}

    def chat_fn(
        message: str,
        history: list,
        provider_key: str,
        enable_tools: bool,
    ):
        prov = next(p for p in _providers() if p.key == provider_key)
        client = make_client(prov)
        if client is None:
            yield (
                f"Configure **{prov.env_api_var}** for this backend, then refresh the page."
            )
            return

        hist = normalize_history(history)
        messages: list[dict[str, Any]] = (
            [{"role": "system", "content": SYSTEM_FLIGHT}] + hist + [{"role": "user", "content": message}]
        )

        use_tools = enable_tools and prov.key == "openai"
        if use_tools:
            yield complete_with_tools(client, prov.default_model, messages)
            return

        for piece in stream_chat(client, prov.default_model, messages, use_tools=False):
            yield piece

    with gr.Blocks(title=f"{PRODUCT_NAME} — Support Console") as app:
        gr.Markdown(
            f"## {PRODUCT_NAME}\n"
            "Ask about flights and fares. Choose a model backend below. "
            "With **Fare lookup** enabled (OpenAI), the agent can query published rates before answering."
        )
        provider = gr.Dropdown(
            choices=[(provider_labels[k], k) for k in provider_keys],
            value="openai",
            label="Model backend",
        )
        tools_toggle = gr.Checkbox(
            value=True,
            label="Fare lookup (OpenAI — uses inventory tool; non-streaming for that path)",
        )
        gr.ChatInterface(
            fn=chat_fn,
            type="messages",
            additional_inputs=[provider, tools_toggle],
        )

    app.launch(inbrowser=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flightai-agent",
        description=f"{PRODUCT_NAME} — console self-test and web support UI.",
    )
    parser.add_argument(
        "command",
        choices=("self-test", "serve", "demo", "ui"),
        help="self-test = console checks; serve = web UI (demo and ui are aliases)",
    )
    args = parser.parse_args()
    cmd = args.command
    if cmd in ("demo", "ui"):
        cmd = "self-test" if cmd == "demo" else "serve"
    if cmd == "self-test":
        run_self_test()
    else:
        launch_console()


if __name__ == "__main__":
    main()

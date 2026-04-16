#!/usr/bin/env python3
"""
FlightAI support agent: chat UI with function calling, SQLite fares, and
read/write tools so the model can quote and update prices in one session.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-4.1-mini"
BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "prices.db"

DEFAULT_FARES = {
    "london": 799,
    "paris": 899,
    "tokyo": 1420,
    "sydney": 2999,
    "berlin": 499,
}

SYSTEM_MESSAGE = """
You are a helpful assistant for an airline called FlightAI.
Give short, courteous answers, no more than 1 sentence when possible.
Always be accurate. If you don't know the answer, say so.
Use tools when the user asks for prices or when they ask you to set or update a fare.
""".strip()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL NOT NULL)"
        )
        conn.commit()


def seed_if_empty() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM prices")
        if cur.fetchone()[0] > 0:
            return
    for city, price in DEFAULT_FARES.items():
        set_ticket_price(city, price)


def get_ticket_price(city: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT price FROM prices WHERE city = ?", (city.lower(),))
        row = cur.fetchone()
    if row:
        return f"Ticket price to {city} is ${row[0]:.0f}"
    return "No price data available for this city"


def set_ticket_price(city: str, price_usd: float) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO prices (city, price) VALUES (?, ?)
            ON CONFLICT(city) DO UPDATE SET price = excluded.price
            """,
            (city.lower(), price_usd),
        )
        conn.commit()
    return f"Updated {city} to ${price_usd:.0f} round trip."


price_tool = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False,
    },
}

set_price_tool = {
    "name": "set_ticket_price",
    "description": "Set or update the round-trip fare in USD for a destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "City name",
            },
            "price_usd": {
                "type": "number",
                "description": "Fare in US dollars",
            },
        },
        "required": ["destination_city", "price_usd"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": price_tool},
    {"type": "function", "function": set_price_tool},
]


def handle_tool_calls(message) -> list[dict]:
    responses: list[dict] = []
    for tool_call in message.tool_calls or []:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")
        if name == "get_ticket_price":
            city = args.get("destination_city", "")
            content = get_ticket_price(city)
        elif name == "set_ticket_price":
            city = args.get("destination_city", "")
            price = float(args.get("price_usd", 0))
            content = set_ticket_price(city, price)
        else:
            content = f"Unknown tool {name}"
        responses.append(
            {
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call.id,
            }
        )
    return responses


def chat(message: str, history: list):
    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        return "Configure OPENAI_API_KEY in your environment."

    init_db()
    seed_if_empty()

    client = OpenAI()
    history_msgs = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = (
        [{"role": "system", "content": SYSTEM_MESSAGE}]
        + history_msgs
        + [{"role": "user", "content": message}]
    )

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)

    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message
        tool_payloads = handle_tool_calls(assistant_message)
        messages.append(assistant_message)
        messages.extend(tool_payloads)
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)

    return response.choices[0].message.content or ""


def main() -> None:
    init_db()
    seed_if_empty()
    gr.ChatInterface(
        fn=chat,
        type="messages",
        title="FlightAI support",
        description="Ask for fares or request updates; the agent uses tools backed by SQLite.",
    ).launch()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FlightAI multimodal desk: tool-backed fare lookup, spoken replies (TTS),
and a destination visual when pricing tools mention a city.
"""

from __future__ import annotations

import base64
import json
import os
import sqlite3
from io import BytesIO
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

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
Use tools when customers ask about ticket prices.
""".strip()

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

TOOLS = [{"type": "function", "function": price_tool}]


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
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO prices (city, price) VALUES (?, ?)
                ON CONFLICT(city) DO UPDATE SET price = excluded.price
                """,
                (city.lower(), price),
            )
            conn.commit()


def get_ticket_price(city: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT price FROM prices WHERE city = ?", (city.lower(),))
        row = cur.fetchone()
    if row:
        return f"Ticket price to {city} is ${row[0]:.0f}"
    return "No price data available for this city"


def handle_tool_calls_and_cities(message) -> tuple[list[dict], list[str]]:
    responses: list[dict] = []
    cities: list[str] = []
    for tool_call in message.tool_calls or []:
        if tool_call.function.name == "get_ticket_price":
            args = json.loads(tool_call.function.arguments or "{}")
            city = args.get("destination_city", "")
            cities.append(city)
            content = get_ticket_price(city)
            responses.append(
                {
                    "role": "tool",
                    "content": content,
                    "tool_call_id": tool_call.id,
                }
            )
    return responses, cities


def talker(client: OpenAI, message: str) -> bytes:
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=message,
    )
    return response.content


def artist(client: OpenAI, city: str) -> Image.Image:
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=(
            f"An image representing a vacation in {city}, showing recognizable landmarks "
            f"and a vibrant pop-art travel poster style"
        ),
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    raw = image_response.data[0].b64_json
    if not raw:
        raise RuntimeError("No image data returned")
    data = base64.b64decode(raw)
    return Image.open(BytesIO(data))


def chat(history: list):
    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        return history, None, None

    init_db()
    seed_if_empty()
    client = OpenAI()

    messages_hist = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}] + messages_hist

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    cities: list[str] = []
    image: Image.Image | None = None

    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message
        tool_msgs, new_cities = handle_tool_calls_and_cities(assistant_message)
        cities.extend(new_cities)
        messages.append(assistant_message)
        messages.extend(tool_msgs)
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)

    reply = response.choices[0].message.content or ""
    updated = history + [{"role": "assistant", "content": reply}]
    voice = talker(client, reply)

    if cities:
        try:
            image = artist(client, cities[0])
        except Exception:  # noqa: BLE001 — keep chat usable if image fails
            image = None

    return updated, voice, image


def put_message_in_chatbot(message: str, history: list):
    return "", history + [{"role": "user", "content": message}]


def main() -> None:
    load_dotenv(override=True)
    init_db()
    seed_if_empty()

    user = os.getenv("GRADIO_USERNAME")
    password = os.getenv("GRADIO_PASSWORD")
    auth = (user, password) if user and password else None

    with gr.Blocks(title="FlightAI multimodal desk") as ui:
        gr.Markdown("## FlightAI multimodal desk\nChat, hear the reply, and see art for priced cities.")
        with gr.Row():
            chatbot = gr.Chatbot(height=480, type="messages")
            image_output = gr.Image(height=480, interactive=False)
        with gr.Row():
            audio_output = gr.Audio(autoplay=True)
        with gr.Row():
            message = gr.Textbox(label="Message", placeholder="Ask for a fare to Paris…")

        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(chat, inputs=chatbot, outputs=[chatbot, audio_output, image_output])

    ui.launch(inbrowser=True, auth=auth)


if __name__ == "__main__":
    main()

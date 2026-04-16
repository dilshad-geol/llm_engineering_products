#!/usr/bin/env python3
"""
Streaming retail concierge chat: multi-turn Gradio UI with a policy-rich system prompt
and a small runtime override when shoppers mention belts.
"""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-4.1-mini"

BASE_SYSTEM = """You are a helpful assistant in a clothes store. You should try to gently encourage \
the customer to try items that are on sale. Hats are 60% off, and most other items are 50% off. \
For example, if the customer says 'I'm looking to buy a hat', \
you could reply something like, 'Wonderful - we have lots of hats - including several that are part of our sales event.'\
Encourage the customer to buy hats if they are unsure what to get.

If the customer asks for shoes, you should respond that shoes are not on sale today, \
but remind the customer to look at hats!"""


def chat(message: str, history: list):
    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        yield "Configure OPENAI_API_KEY in your environment."
        return

    client = OpenAI()
    history_msgs = [{"role": h["role"], "content": h["content"]} for h in history]

    relevant_system = BASE_SYSTEM
    if "belt" in message.lower():
        relevant_system += (
            " The store does not sell belts; if you are asked for belts, "
            "be sure to point out other items on sale."
        )

    messages = (
        [{"role": "system", "content": relevant_system}]
        + history_msgs
        + [{"role": "user", "content": message}]
    )

    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response


def main() -> None:
    gr.ChatInterface(
        fn=chat,
        type="messages",
        title="Concierge chat",
        description="Ask about apparel, sales, or sizing. Streaming replies.",
    ).launch()


if __name__ == "__main__":
    main()

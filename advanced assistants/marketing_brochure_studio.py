#!/usr/bin/env python3
"""
Gradio app: stream a short markdown brochure from a company landing page,
using either OpenAI or Anthropic via the OpenAI-compatible client pattern.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

# Repo root → experiments/ for scraper_core (same helper as experiments/*.py demos)
_ROOT = Path(__file__).resolve().parent
_EXPERIMENTS = _ROOT.parent / "experiments"
if str(_EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENTS))

from scraper_core import fetch_website_contents

BROCHURE_SYSTEM = """You are an assistant that analyzes the contents of a company website landing page
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks."""


def _clients() -> tuple[OpenAI, OpenAI]:
    load_dotenv(override=True)
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not openai_key or not anthropic_key:
        missing = []
        if not openai_key:
            missing.append("OPENAI_API_KEY")
        if not anthropic_key:
            missing.append("ANTHROPIC_API_KEY")
        raise RuntimeError("Missing: " + ", ".join(missing))

    openai = OpenAI()
    anthropic = OpenAI(api_key=anthropic_key, base_url="https://api.anthropic.com/v1/")
    return openai, anthropic


def stream_openai(openai: OpenAI, user_prompt: str):
    messages = [
        {"role": "system", "content": BROCHURE_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    stream = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        stream=True,
    )
    buf = ""
    for chunk in stream:
        buf += chunk.choices[0].delta.content or ""
        yield buf


def stream_anthropic(anthropic: OpenAI, user_prompt: str):
    messages = [
        {"role": "system", "content": BROCHURE_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    stream = anthropic.chat.completions.create(
        model="claude-sonnet-4-5-20250929",
        messages=messages,
        stream=True,
    )
    buf = ""
    for chunk in stream:
        buf += chunk.choices[0].delta.content or ""
        yield buf


def stream_brochure(company_name: str, url: str, model: str):
    yield ""
    try:
        page = fetch_website_contents(url)
    except Exception as exc:  # noqa: BLE001 — surface fetch errors in the UI
        yield f"Could not fetch the page: {exc}"
        return

    prompt = f"Please generate a company brochure for {company_name}. Here is their landing page:\n{page}"
    openai, anthropic = _clients()
    if model == "GPT":
        yield from stream_openai(openai, prompt)
    elif model == "Claude":
        yield from stream_anthropic(anthropic, prompt)
    else:
        yield "Unknown model selection."


def build_app() -> gr.Interface:
    _clients()  # Fail fast on startup if keys missing

    name_input = gr.Textbox(label="Company name")
    url_input = gr.Textbox(label="Landing page URL (https://…)")
    model_selector = gr.Dropdown(["GPT", "Claude"], label="Model", value="GPT")
    out = gr.Markdown(label="Brochure")

    return gr.Interface(
        fn=stream_brochure,
        title="Brochure studio",
        description="Paste a public landing page URL and stream a concise positioning brief.",
        inputs=[name_input, url_input, model_selector],
        outputs=[out],
        examples=[
            ["Hugging Face", "https://huggingface.co", "GPT"],
            ["Anthropic", "https://www.anthropic.com", "Claude"],
        ],
        flagging_mode="never",
    )


def main() -> None:
    app = build_app()
    app.launch()


if __name__ == "__main__":
    main()

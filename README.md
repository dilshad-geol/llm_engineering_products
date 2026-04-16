# LLM Engineering — Products & Experiments

This repository collects **products** and **experiments** built while working in **LLM engineering**: designing, shipping, and evaluating systems that use large language models in real workflows.

## Repository layout

| Location | What it is |
|----------|------------|
| [`advanced assistants/`](advanced%20assistants/) | **FlightAI Virtual Agent** — a richer assistant demo: multi-provider routing, streaming chat, **function calling** (fare lookup against in-memory inventory), and a **Gradio** support console. |
| [`experiments/`](experiments/) | Short, single-purpose scripts (API basics, tokens, Ollama vs OpenAI, web → LLM pipelines, small assistants). |

---

## Advanced assistants — FlightAI Virtual Agent

[`advanced assistants/advanced_portfolio_assistant.py`](advanced%20assistants/advanced_portfolio_assistant.py) implements **FlightAI Virtual Agent**: customer-support style chat with optional **tool use** (published return fares from a small SQLite-backed inventory), **token streaming** in the UI, and **model routing** through one OpenAI-compatible client surface:

- **OpenAI** (default; required for full self-test and for **fare lookup** in the UI)
- **Anthropic** (OpenAI-compatible endpoint)
- **Google Gemini** (OpenAI-compatible endpoint)

**Environment**

- `OPENAI_API_KEY` — fare tool and recommended for self-test / streaming samples  
- `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` — optional alternate backends  
- `OPENAI_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL` — optional overrides  

**Dependencies** (see imports in the file): `openai`, `python-dotenv`, `gradio` for the web UI.

**Run from the repository root** (quote the path because of the space in the directory name):

```bash
python "advanced assistants/advanced_portfolio_assistant.py" self-test
python "advanced assistants/advanced_portfolio_assistant.py" serve
```

`self-test` runs connectivity checks, a streaming sample, and the fare-tool path (when OpenAI is configured). `serve` opens the Gradio support console in the browser (`demo` / `ui` are accepted aliases for those commands). With **Fare lookup** enabled in the UI, only the **OpenAI** backend runs the tool path (non-streaming for that flow); other providers use streaming chat without that demo tool.

---

## `experiments/` — scripts and demos

All **runnable Python experiments** in this folder are short, self-contained scripts for chat APIs, token math, comparing hosted OpenAI with local Ollama, scraping web text into prompts, and structured JSON-style outputs. Each one is meant to **try a single idea end-to-end** (prompt ± fetch ± model). This folder is not an installable package—just runnable examples you can copy from or extend.

Run from the **repository root**, for example:

```bash
python experiments/openai_chat_sdk_minimal.py "Your prompt here"
```

Each script has a **module docstring** at the top (purpose, env vars, notes). The shared helper for URL-based demos is `experiments/scraper_core.py`.

### Shared utilities

| Script | What it does |
|--------|----------------|
| `experiments/scraper_core.py` | Fetch public URLs, strip noisy HTML, return plain text (and link lists) for prompts. Used by several site-based demos below. |

### Chat API basics (OpenAI & HTTP)

| Script | What it does |
|--------|----------------|
| `experiments/openai_chat_sdk_minimal.py` | Smallest Chat Completions example with the official OpenAI Python SDK. |
| `experiments/chat_completion_raw_http.py` | Same idea via raw `requests` to `/v1/chat/completions` (no SDK). |
| `experiments/multi_turn_chat_with_explicit_history.py` | Interactive REPL: shows **stateless** chat by replaying full `messages` each turn. |

### Tokens, cost, and context size

| Script | What it does |
|--------|----------------|
| `experiments/conversation_token_growth_demo.py` | Uses **tiktoken** only (no LLM call): shows how token counts grow as chat history lengthens. |
| `experiments/token_budget_estimator.py` | Count tokens and apply **illustrative** per-1K rates for rough USD estimates. |

### Local Ollama vs hosted OpenAI

| Script | What it does |
|--------|----------------|
| `experiments/ollama_chat_smoke_test.py` | Quick health check against the local OpenAI-compatible Ollama endpoint. |
| `experiments/technical_explainer_dual_backend.py` | Answer a technical question using **either** OpenAI or Ollama. |
| `experiments/web_digest_local_ollama.py` | Scrape a URL and summarize with a **local** model (Ollama). |
| `experiments/compare_hosted_and_local_summary.py` | Same scraped page summarized side by side with **OpenAI and Ollama** for comparison. |

### Web → text → LLM (briefs, intel, content)

These use `scraper_core` in `experiments/` plus OpenAI unless noted. Set **`OPENAI_API_KEY`** (often with a `.env` via `python-dotenv`).

| Script | What it does |
|--------|----------------|
| `experiments/executive_web_digest_openai.py` | Public URL → short **stakeholder-ready Markdown** brief. |
| `experiments/company_brochure_from_website.py` | Homepage + model-chosen links → **Markdown brochure** (multi-page pattern). |
| `experiments/diligence_link_curator.py` | Homepage links → **JSON shortlist** for due diligence / partnership review. |
| `experiments/careers_page_recruiter_brief.py` | Careers URL → hiring signals (roles, remote, stack hints, process clues). |
| `experiments/pricing_page_positioning_snapshot.py` | Pricing URL → plans, limits, positioning snapshot. |
| `experiments/documentation_portal_digest.py` | Docs landing page → orientation (sections, quickstarts, API hints). |
| `experiments/product_changelog_to_release_brief.py` | Changelog / release-notes URL → **PM-style release summary**. |
| `experiments/snarky_web_review.py` | Same scrape → **humorous** Markdown take (tone experiment). |

### Structured outputs & assistants

| Script | What it does |
|--------|----------------|
| `experiments/structured_support_triage.py` | Customer message → **JSON** routing metadata (category, priority, etc.). |
| `experiments/email_subject_line_assistant.py` | Draft email body → suggested **subject line**. |

## Setup (quick)

- **Python 3** and packages imported by each script (commonly: `openai`, `python-dotenv`, `requests`, `beautifulsoup4`, `tiktoken` for the experiments; **`gradio`** for the FlightAI console).
- **OpenAI**: set `OPENAI_API_KEY` in the environment or `.env` for hosted runs.
- **Ollama**: run `ollama serve`, pull a model (e.g. `llama3.2`), and point scripts at your local base URL when required.

There is no single `requirements.txt` yet; dependencies match each file’s imports.

## Broader themes (roadmap)

Work here also touches ideas that are not all represented as separate scripts yet:

- **RAG** — chunking, embeddings, vector stores, re-ranking, evaluation  
- **Agents & tools** — multi-step flows beyond single-shot chat *(see **FlightAI Virtual Agent** for tool calling and follow-up turns)*  
- **Eval & observability** — test sets, quality metrics, tracing  

---

*Work in progress — new experiments and products will be added over time.*

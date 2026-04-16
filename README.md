# LLM Engineering — Products & Experiments

This repository collects **products** and **experiments** built while working in **LLM engineering**: designing, shipping, and evaluating systems that use large language models in real workflows.

## `llm_lab/` — LLM engineering lab

All current **runnable Python experiments** live in [`llm_lab/`](llm_lab/). That folder is the **lab**: short, self-contained scripts for chat APIs, token math, comparing hosted OpenAI with local Ollama, scraping web text into prompts, and structured JSON-style outputs. It is a place to **try ideas end-to-end** (prompt ± fetch ± model), not a single installable library.

Run from the **repository root**, for example:

```bash
python llm_lab/openai_chat_sdk_minimal.py "Your prompt here"
```

Each script has a **module docstring** at the top (purpose, env vars, notes). The shared helper for URL-based demos is `llm_lab/scraper_core.py`.

### Shared utilities

| Script | What it does |
|--------|----------------|
| `llm_lab/scraper_core.py` | Fetch public URLs, strip noisy HTML, return plain text (and link lists) for prompts. Used by several site-based demos below. |

### Chat API basics (OpenAI & HTTP)

| Script | What it does |
|--------|----------------|
| `llm_lab/openai_chat_sdk_minimal.py` | Smallest Chat Completions example with the official OpenAI Python SDK. |
| `llm_lab/chat_completion_raw_http.py` | Same idea via raw `requests` to `/v1/chat/completions` (no SDK). |
| `llm_lab/multi_turn_chat_with_explicit_history.py` | Interactive REPL: shows **stateless** chat by replaying full `messages` each turn. |

### Tokens, cost, and context size

| Script | What it does |
|--------|----------------|
| `llm_lab/conversation_token_growth_demo.py` | Uses **tiktoken** only (no LLM call): shows how token counts grow as chat history lengthens. |
| `llm_lab/token_budget_estimator.py` | Count tokens and apply **illustrative** per-1K rates for rough USD estimates. |

### Local Ollama vs hosted OpenAI

| Script | What it does |
|--------|----------------|
| `llm_lab/ollama_chat_smoke_test.py` | Quick health check against the local OpenAI-compatible Ollama endpoint. |
| `llm_lab/technical_explainer_dual_backend.py` | Answer a technical question using **either** OpenAI or Ollama. |
| `llm_lab/web_digest_local_ollama.py` | Scrape a URL and summarize with a **local** model (Ollama). |
| `llm_lab/compare_hosted_and_local_summary.py` | Same scraped page summarized side by side with **OpenAI and Ollama** for comparison. |

### Web → text → LLM (briefs, intel, content)

These use `scraper_core` in `llm_lab/` plus OpenAI unless noted. Set **`OPENAI_API_KEY`** (often with a `.env` via `python-dotenv`).

| Script | What it does |
|--------|----------------|
| `llm_lab/executive_web_digest_openai.py` | Public URL → short **stakeholder-ready Markdown** brief. |
| `llm_lab/company_brochure_from_website.py` | Homepage + model-chosen links → **Markdown brochure** (multi-page pattern). |
| `llm_lab/diligence_link_curator.py` | Homepage links → **JSON shortlist** for due diligence / partnership review. |
| `llm_lab/careers_page_recruiter_brief.py` | Careers URL → hiring signals (roles, remote, stack hints, process clues). |
| `llm_lab/pricing_page_positioning_snapshot.py` | Pricing URL → plans, limits, positioning snapshot. |
| `llm_lab/documentation_portal_digest.py` | Docs landing page → orientation (sections, quickstarts, API hints). |
| `llm_lab/product_changelog_to_release_brief.py` | Changelog / release-notes URL → **PM-style release summary**. |
| `llm_lab/snarky_web_review.py` | Same scrape → **humorous** Markdown take (tone experiment). |

### Structured outputs & assistants

| Script | What it does |
|--------|----------------|
| `llm_lab/structured_support_triage.py` | Customer message → **JSON** routing metadata (category, priority, etc.). |
| `llm_lab/email_subject_line_assistant.py` | Draft email body → suggested **subject line**. |

## Setup (quick)

- **Python 3** and packages imported by each script (commonly: `openai`, `python-dotenv`, `requests`, `beautifulsoup4`, `tiktoken` for the scripts that need them).
- **OpenAI**: set `OPENAI_API_KEY` in the environment or `.env` for hosted runs.
- **Ollama**: run `ollama serve`, pull a model (e.g. `llama3.2`), and point scripts at your local base URL when required.

There is no single `requirements.txt` yet; dependencies match each file’s imports.

## Broader themes (roadmap)

Work here also touches ideas that are not all represented as separate scripts yet:

- **RAG** — chunking, embeddings, vector stores, re-ranking, evaluation  
- **Agents & tools** — multi-step flows beyond single-shot chat  
- **Eval & observability** — test sets, quality metrics, tracing  

---

*Work in progress — new experiments and products will be added over time.*

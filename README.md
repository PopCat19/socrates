# Socrates

Prompt assistant that generates ranked clarifying questions as you type,
with extended reasoning on demand.

## What it does

- Debounces LLM calls (~400ms) to generate P0–P2 clarifying questions from partial prompts
- Ctrl+Enter (web/TUI) triggers a streamed extended reasoning response
- Model selector fetches from API; falls back to text input if unavailable
- Shared Python backend serves both a Textual TUI and a Vite/TypeScript web UI

## Stack

| Layer | Tech |
|-------|------|
| API server | FastAPI + uvicorn |
| TUI | Textual |
| Web UI | Vite + TypeScript |
| LLM client | httpx, OpenAI-compatible |
| Package mgr | Nix flake + bun |

## Quickstart

**With Nix:**
```bash
nix develop
```

**Without Nix:**
```bash
pip install -e .
cd web && bun install
```

**Run:**
```bash
# API server (required for both clients)
PYTHONPATH=. python server/main.py

# TUI
PYTHONPATH=. python tui/main.py

# Web dev server (proxies /api → :7384)
cd web && bun run dev
```

Open [localhost:5173](http://localhost:5173) for the web UI.

## Config

| Var | Default | Purpose |
|-----|---------|---------|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Ollama or OpenAI-compatible endpoint |
| `LLM_API_KEY` | `ollama` | API key |
| `LLM_MODEL` | _(first from API)_ | TUI default model |
| `PORT` | `7384` | Server port |

## Structure

```
socrates/
├── server/         # FastAPI server + static file serving
├── shared/         # LLM client and prompt logic (used by both clients)
├── tui/            # Textual TUI
└── web/            # Vite/TypeScript web UI
```

# Agents

## Project Overview

Magazine Scraper — a pipeline that scrapes a magazine website into an EPUB file.

## Setup

```bash
uv sync
uv run playwright install chromium
```

## Commands

- **Run tests:** `uv run pytest`
- **Lint:** `uv run ruff check .`
- **Format check:** `uv run ruff format --check .`
- **Type check:** `uv run ty check`
- **Run pipeline:** `uv run python -m magazine_scraper.pipeline <toc-url>`

## Code Conventions

- Use **dataclasses** for data models (see `models.py`).
- **No async APIs.** Use synchronous functions throughout; do not use `async`/`await` or `asyncio`.
- Use **type hints** on all function signatures.
- **Rate limiting.** Add a one-second sleep (`time.sleep(1)`) after every network call to comply with rate limiting.
- Pre-commit hooks handle linting, formatting, and type checking automatically.

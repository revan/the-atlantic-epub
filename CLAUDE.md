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
- **Run pipeline (CLI):** `uv run python -m magazine_scraper.pipeline <toc-url>`
- **Run server locally:** `uv run uvicorn magazine_scraper.server:app --reload`
- **Build and run the container:** `docker compose up -d --build`
- **Run the frontend dev server:** `cd frontend && npm run dev` (proxies the API to port 8000)
- **Frontend build and tests:** `cd frontend && npm run build` / `npm test`

## Code Conventions

- Use **dataclasses** for data models (see `models.py`).
- **No async APIs.** Use synchronous functions throughout; do not use `async`/`await` or `asyncio`.
- Use **type hints** on all function signatures.
- **Rate limiting.** Add a one-second sleep (`time.sleep(1)`) after every network call to comply with rate limiting.
- **No login.** Scraping runs anonymously on purpose; see the docstring in `auth.py`. Do not add a credential flow — the site's reCAPTCHA rejects it.
- **`wait_until`.** Never use `networkidle` on theatlantic.com; it never settles. Use `domcontentloaded`.
- Pre-commit hooks handle linting, formatting, and type checking automatically.

## Frontend

- Lives in `frontend/`; React + Vite + Tailwind + **shadcn/ui** components under `src/components/ui`.
- `epubFilename` in `src/issues.ts` must stay in sync with `url_to_filename` in `pipeline.py` —
  the UI joins files to issues by that exact string.
- Talk to the API with relative paths only, so the Vite proxy and the mounted bundle both work.

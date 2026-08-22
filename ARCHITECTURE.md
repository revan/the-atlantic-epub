# Architecture

## Overview

Magazine Scraper scrapes a magazine website and assembles the content into an EPUB file. It navigates the magazine's table of contents, extracts each article's content, and packages everything into a portable ebook format. The pipeline runs either from the CLI or behind a FastAPI server that queues scrapes and serves the resulting files, with a React frontend served from the same origin.

## Pipeline Phases

1. **TOC Scraping** — Navigate to the magazine issue page and extract the list of article URLs and titles.
2. **Article Scraping** — Visit each article URL and extract the HTML body content.
3. **EPUB Assembly** — Combine all scraped articles into a well-structured EPUB file.

## Modules

| Module | Purpose |
|---|---|
| `magazine_scraper/models.py` | Data models (`Article`, `TableOfContents`) as dataclasses |
| `magazine_scraper/scraper.py` | Synchronous scraping functions using Playwright |
| `magazine_scraper/epub_builder.py` | EPUB file assembly using ebooklib |
| `magazine_scraper/pipeline.py` | Main orchestrator that chains the pipeline phases |
| `magazine_scraper/auth.py` | Browser context for scraping (no login — see the README) |
| `magazine_scraper/jobs.py` | Background scrape queue, one worker at a time |
| `magazine_scraper/server.py` | FastAPI app: list files, download a file, scrape a month |
| `magazine_scraper/backfill.py` | Walks the issue sitemap and runs the pipeline for each |
| `frontend/` | React UI: a card per issue, scrape and download |

## Tech Stack

- **uv** — Python package and project manager
- **Playwright** — Browser automation for scraping
- **ebooklib** — EPUB file generation
- **BeautifulSoup4 + lxml** — HTML parsing and content extraction
- **FastAPI + Uvicorn** — HTTP service
- **React + Vite + Tailwind + shadcn/ui** — Frontend, built into the image and mounted at `/`
- **pytest** and **Vitest** — Testing
- **ruff** — Linting and formatting
- **ty** — Type checking

## Running

As a server (see the README for the endpoints):

```bash
docker compose up -d --build
```

As a one-off from the CLI:

```bash
uv run python -m magazine_scraper.pipeline <toc-url>
```

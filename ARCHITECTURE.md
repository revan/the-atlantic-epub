# Architecture

## Overview

Magazine Scraper is a pipeline that scrapes a magazine website and assembles the content into an EPUB file. It navigates the magazine's table of contents, extracts each article's content, and packages everything into a portable ebook format.

## Pipeline Phases

1. **TOC Scraping** — Navigate to the magazine issue page and extract the list of article URLs and titles.
2. **Article Scraping** — Visit each article URL and extract the HTML body content.
3. **EPUB Assembly** — Combine all scraped articles into a well-structured EPUB file.

## Modules

| Module | Purpose |
|---|---|
| `magazine_scraper/models.py` | Data models (`Article`, `TableOfContents`) as dataclasses |
| `magazine_scraper/scraper.py` | Async scraping functions using Playwright |
| `magazine_scraper/epub_builder.py` | EPUB file assembly using ebooklib |
| `magazine_scraper/pipeline.py` | Main orchestrator that chains the pipeline phases |

## Tech Stack

- **uv** — Python package and project manager
- **Playwright** — Browser automation for scraping
- **ebooklib** — EPUB file generation
- **BeautifulSoup4 + lxml** — HTML parsing and content extraction
- **pytest** — Testing
- **ruff** — Linting and formatting
- **ty** — Type checking

## Running

```bash
uv run python -m magazine_scraper.pipeline <toc-url>
```

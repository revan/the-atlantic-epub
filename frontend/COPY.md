# UI copy

Every user-visible string in the frontend, as it now reads. Edit the **After** column
(`unchanged` to leave a row alone, empty to delete the string), and I'll apply it.

Items 16–23 come from the Python server, not the frontend — the card prints them
verbatim, so changing them means editing `magazine_scraper/`.

## Browser tab

| # | Where | Now | After |
|---|---|---|---|
| 1 | `index.html:8` | The Atlantic EPUB | unchanged |

## Page header

| # | Where | Now | After |
|---|---|---|---|
| 2 | `App.tsx` heading | The Atlantic | unchanged |
| 3 | `App.tsx` subtitle, while loading | Loading issues… | unchanged |
| 4 | `App.tsx` subtitle, loaded | 2 issues scraped | unchanged |

## Card — status line

| # | Where | Now | After |
|---|---|---|---|
| 5 | Issue name | September 2026 | unchanged |
| 6 | Status, never scraped | Not scraped | unchanged |
| 7 | Badge, failed | Failed | unchanged |
| 8 | Status, waiting for the worker | queued | unchanged |
| 9 | Status, running | scraping articles 12/15 | unchanged |
| 10 | File size | 0.2 MB | unchanged |
| 11 | Scrape date | Aug 22, 2026, 2:16 PM | unchanged |

Both 10 and 11 are formats rather than fixed text — 10 is megabytes to one decimal,
11 is the browser's medium date + short time in the reader's own locale.

A scraped card carries no badge: its filename, date, size, and **Download** button are
what mark it as done.

## Card — buttons

| # | Where | Now | After |
|---|---|---|---|
| 12 | Never scraped | Scrape | unchanged |
| 13 | While running, disabled | Scraping | unchanged |
| 14 | Already scraped | Re-scrape | unchanged |
| 15 | Already scraped | Download | unchanged |

## Progress steps — from the server

These are `job.step` values printed straight into row 9.

| # | Where | Now | After |
|---|---|---|---|
| 16 | `jobs.py:96` | starting | unchanged |
| 17 | `pipeline.py:67` | scraping table of contents | unchanged |
| 18 | `pipeline.py:78` | downloading cover image | unchanged |
| 19 | `pipeline.py:87` | scraping articles | unchanged |
| 20 | `pipeline.py:98` | building EPUB | unchanged |

## Error text — from the server

Printed straight after the **Failed** badge.

| # | Where | Now | After |
|---|---|---|---|
| 21 | `jobs.py:66`, duplicate scrape | 2026-09 is already running as job a1b2c3… | unchanged |
| 22 | `jobs.py:111`, scrape failed | RuntimeError: no issue published for this month | unchanged |
| 23 | `api.ts`, request failed with no detail | 404 Not Found | unchanged |

Item 22 prefixes the Python exception class name, so a reader sees `TimeoutError:`,
`PlaywrightError:` and the like. Worth deciding whether that belongs in front of a
reader or only in the logs.

## Not copy, but adjacent

A finished scrape briefly reads **Not scraped** — the job flips to `done` one render
before the file list refreshes and the card flips to its scraped state. Say the word
and I'll hold the running state until the file arrives.

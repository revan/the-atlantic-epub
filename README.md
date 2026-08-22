# The Atlantic.epub

Scrapes full issues of The Atlantic magazine into EPUB files, with cover art, a table of
contents, and article subtitles and bylines — but no images within the articles.

Runs as a small HTTP service in Docker with a web UI: browse every issue back to November
1857, scrape the ones you want, and download the EPUBs it has built.

Bring your own subscription; good journalism is worth paying for!

## Running

```bash
docker compose up -d --build
```

Open `http://localhost:8000` for the UI. The API is on the same port, with interactive docs
at `/docs`. EPUBs are written to the `atlantic-data` volume at `/data/output` and survive
restarts.

## The UI

A card per issue, newest first: the list opens on next month's issue — the magazine publishes
ahead of the calendar — and scrolls back to the first issue in November 1857. An issue that has
not been scraped gets a **Scrape** button; one that has shows its filename, when it was scraped,
its size, and a **Download** link.

Cards read their state from `/files`, so a scraped issue stays scraped across restarts. Progress
on a running scrape comes from `/jobs`, which is in-memory and resets with the server.

Not every month has an issue — the magazine combines months in recent years, and its early
decades varied — so some cards will fail to scrape. The card keeps the error.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/files` | List generated EPUBs with size and modification time |
| `GET` | `/files/{filename}` | Download one EPUB |
| `POST` | `/scrape` | Queue a scrape — body `{"year": 2026, "month": 9}` |
| `GET` | `/jobs` | Every scrape job since the server started, newest first |
| `GET` | `/jobs/{id}` | Status and per-article progress of one job |

Scraping an issue takes a few minutes, so `POST /scrape` returns `202` with a job id
immediately and the work happens in the background:

```bash
curl -X POST localhost:8000/scrape -H 'content-type: application/json' \
  -d '{"year":2026,"month":9}'
curl localhost:8000/jobs/<id>
curl -O -J 'localhost:8000/files/The%20Atlantic%202026-09.epub'
```

Filenames embed the issue as `The Atlantic YYYY-MM.epub`, so they sort chronologically in
a reader's library.

Jobs run one at a time. That is deliberate: it keeps the scraper's one-second delay between
requests meaningful and holds only one browser in memory. Requesting an issue that is
already queued or running returns `409`.

Job history lives in memory and is empty again after a restart — the EPUBs on the volume are
the durable output.

## Notes

**No login is required.** The Atlantic's paywall is a client-side metered overlay: the full
article text is server-rendered into the page on every request, and the scraper reads the
raw DOM, so the overlay never applies. Verified against issues from 2015 through 2026.

Signing in automatically is not an option anyway — the account form is protected by
reCAPTCHA, which rejects Playwright-driven submissions with `invalid_recaptcha` whether the
browser is headless or headed.

**There is no API authentication.** Run this on a trusted network only.

## Development

See [CLAUDE.md](CLAUDE.md) for the local `uv` workflow and [ARCHITECTURE.md](ARCHITECTURE.md)
for the module layout.

The frontend lives in `frontend/` (React + Vite + shadcn/ui). For local work, run the API and the
Vite dev server side by side — Vite proxies the API routes to port 8000, so there is no CORS
setup:

```bash
uv run uvicorn magazine_scraper.server:app --reload
```

```bash
cd frontend && npm install && npm run dev
```

`docker compose build` compiles the bundle in a Node stage and the server mounts it at `/`; a
checkout without a build simply has no UI, and the API is unaffected.

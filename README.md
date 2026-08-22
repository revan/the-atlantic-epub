# The Atlantic.epub

Scrapes full issues of The Atlantic magazine into EPUB files, with cover art, a table of
contents, and article subtitles and bylines — but no images within the articles.

Runs as a small HTTP service in Docker: ask it to scrape a month, then list and download
the EPUBs it has built.

Bring your own subscription; good journalism is worth paying for!

## Running

```bash
docker compose up -d --build
```

The API listens on `http://localhost:8000`; interactive docs are at `/docs`. EPUBs are
written to the `atlantic-data` volume at `/data/output` and survive restarts.

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

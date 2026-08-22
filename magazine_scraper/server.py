"""FastAPI server exposing the scraper as a long-running service.

Endpoints cover the three things the service is for: list the EPUBs on
disk, download one, and scrape an issue for a given month. The built
frontend, if one was compiled into the image, is served from ``/``.

There is no API authentication: run this on a trusted network only.
"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from magazine_scraper import jobs

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "/data/output"
DEFAULT_FRONTEND_DIR = "/app/static"
EPUB_MEDIA_TYPE = "application/epub+zip"


def output_dir() -> Path:
    """Directory holding generated EPUBs."""
    return Path(os.environ.get("OUTPUT_DIR", DEFAULT_OUTPUT_DIR))


def frontend_dir() -> Path:
    """Directory holding the built frontend, if one was compiled in."""
    return Path(os.environ.get("FRONTEND_DIR", DEFAULT_FRONTEND_DIR))


class EpubFile(BaseModel):
    name: str
    size_bytes: int
    modified: datetime


class ScrapeRequest(BaseModel):
    year: int = Field(ge=1857, le=2100, description="Issue year")
    month: int = Field(ge=1, le=12, description="Issue month, 1-12")


class JobResponse(BaseModel):
    id: str
    year: int
    month: int
    toc_url: str
    status: str
    step: str
    message: str
    articles_done: int
    articles_total: int
    filename: str | None
    created_at: datetime
    finished_at: datetime | None


def _job_response(job: jobs.Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        year=job.year,
        month=job.month,
        toc_url=job.toc_url,
        status=job.status,
        step=job.step,
        message=job.message,
        articles_done=job.articles_done,
        articles_total=job.articles_total,
        filename=job.filename,
        created_at=datetime.fromtimestamp(job.created_at, UTC),
        finished_at=(
            datetime.fromtimestamp(job.finished_at, UTC) if job.finished_at is not None else None
        ),
    )


def _resolve_epub(filename: str) -> Path:
    """Resolve a requested filename inside the output directory.

    Rejects anything that escapes the directory or is not an EPUB.
    """
    base = output_dir().resolve()
    candidate = (base / filename).resolve()
    if candidate.parent != base or candidate.suffix != ".epub" or not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"No such EPUB: {filename}")
    return candidate


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    directory = output_dir()
    directory.mkdir(parents=True, exist_ok=True)
    logger.info("Serving EPUBs from %s", directory)
    yield


app = FastAPI(
    title="The Atlantic EPUB scraper",
    description="Scrapes issues of The Atlantic into EPUB files.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/files")
def list_files() -> list[EpubFile]:
    """List generated EPUBs, oldest issue first.

    Filenames embed the issue as ``YYYY-MM``, so sorting by name is
    chronological.
    """
    directory = output_dir()
    if not directory.is_dir():
        return []

    files = []
    for path in sorted(directory.glob("*.epub")):
        stat = path.stat()
        files.append(
            EpubFile(
                name=path.name,
                size_bytes=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime, UTC),
            )
        )
    return files


@app.get("/files/{filename}")
def download_file(filename: str) -> FileResponse:
    """Download one EPUB."""
    path = _resolve_epub(filename)
    return FileResponse(path, media_type=EPUB_MEDIA_TYPE, filename=path.name)


@app.post("/scrape", status_code=202)
def scrape(request: ScrapeRequest) -> JobResponse:
    """Queue a scrape of one month's issue."""
    try:
        job = jobs.submit(request.year, request.month, output_dir())
    except jobs.DuplicateJobError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _job_response(job)


@app.get("/jobs")
def list_jobs() -> list[JobResponse]:
    """Every scrape job since the server started, newest first."""
    return [_job_response(job) for job in jobs.all_jobs()]


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> JobResponse:
    """Status and progress of one scrape job."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No such job: {job_id}")
    return _job_response(job)


# Mounted last so every API route above keeps priority over the catch-all, and
# only when a bundle exists — running uvicorn from a checkout has no build.
_frontend = frontend_dir()
if _frontend.is_dir():
    logger.info("Serving frontend from %s", _frontend)
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="frontend")

"""Background scrape jobs.

A full issue takes minutes to scrape, so the API hands the work to a single
worker thread and reports progress by job id.  One worker is deliberate: it
keeps the pipeline's one-second rate limiting meaningful across concurrent
requests and holds at most one Chromium in memory.

Job state lives in memory and resets when the process restarts; the EPUBs on
disk are the durable output.
"""

import logging
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from magazine_scraper.pipeline import month_to_toc_url, run_pipeline

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = ("queued", "running")


class DuplicateJobError(RuntimeError):
    """Raised when an issue is already queued or being scraped."""


@dataclass
class Job:
    id: str
    year: int
    month: int
    toc_url: str
    output_dir: str
    status: str = "queued"  # queued | running | done | failed
    step: str = ""
    message: str = ""
    articles_done: int = 0
    articles_total: int = 0
    filename: str | None = None
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None


_jobs: dict[str, Job] = {}
_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scrape")


def submit(year: int, month: int, output_dir: Path) -> Job:
    """Queue a scrape for one issue.

    Raises ``DuplicateJobError`` when that issue is already in flight.
    """
    with _lock:
        for existing in _jobs.values():
            if (
                existing.year == year
                and existing.month == month
                and existing.status in ACTIVE_STATUSES
            ):
                raise DuplicateJobError(
                    f"{year}-{month:02d} is already {existing.status} as job {existing.id}"
                )

        job = Job(
            id=uuid.uuid4().hex,
            year=year,
            month=month,
            toc_url=month_to_toc_url(year, month),
            output_dir=str(output_dir),
        )
        _jobs[job.id] = job

    _executor.submit(_run, job)
    logger.info("Queued job %s for %d-%02d", job.id, year, month)
    return job


def get(job_id: str) -> Job | None:
    """Look up a job by id."""
    return _jobs.get(job_id)


def all_jobs() -> list[Job]:
    """Every job this process knows about, newest first."""
    return sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)


def _run(job: Job) -> None:
    job.status = "running"
    job.step = "starting"

    def progress(step: str, done: int, total: int) -> None:
        job.step = step
        if total:
            job.articles_done = done
            job.articles_total = total

    try:
        path = run_pipeline(job.toc_url, Path(job.output_dir), progress=progress)
        job.filename = path.name
        job.status = "done"
        job.step = "complete"
        logger.info("Job %s wrote %s", job.id, path)
    except Exception as exc:
        job.status = "failed"
        job.message = f"{type(exc).__name__}: {exc}"
        logger.error("Job %s failed:\n%s", job.id, traceback.format_exc())
    finally:
        job.finished_at = time.time()

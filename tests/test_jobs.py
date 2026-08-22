import time
from pathlib import Path

import pytest

from magazine_scraper import jobs


@pytest.fixture(autouse=True)
def clean_registry():
    """Each test starts with an empty job registry."""
    jobs._jobs.clear()
    yield
    jobs._jobs.clear()


def wait_for(job: jobs.Job, status: str, timeout: float = 5.0) -> jobs.Job:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if job.status == status:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job stayed {job.status!r}, never reached {status!r}")


def test_submit_runs_pipeline_and_records_filename(tmp_path: Path, monkeypatch):
    def fake_pipeline(toc_url, output_dir, progress=None):
        assert toc_url == "https://www.theatlantic.com/magazine/toc/2026/09/"
        if progress:
            progress("scraping articles", 3, 17)
        return Path(output_dir) / "The Atlantic 2026-09.epub"

    monkeypatch.setattr(jobs, "run_pipeline", fake_pipeline)

    job = jobs.submit(2026, 9, tmp_path)
    wait_for(job, "done")
    assert job.filename == "The Atlantic 2026-09.epub"
    assert job.articles_done == 3
    assert job.articles_total == 17
    assert job.finished_at is not None


def test_failed_pipeline_records_message(tmp_path: Path, monkeypatch):
    def boom(toc_url, output_dir, progress=None):
        raise RuntimeError("scrape exploded")

    monkeypatch.setattr(jobs, "run_pipeline", boom)

    job = jobs.submit(2026, 9, tmp_path)
    wait_for(job, "failed")
    assert "scrape exploded" in job.message
    assert job.filename is None


def test_duplicate_month_is_rejected_while_active(tmp_path: Path, monkeypatch):
    release = 0.2

    def slow(toc_url, output_dir, progress=None):
        time.sleep(release)
        return Path(output_dir) / "x.epub"

    monkeypatch.setattr(jobs, "run_pipeline", slow)

    jobs.submit(2026, 9, tmp_path)
    with pytest.raises(jobs.DuplicateJobError):
        jobs.submit(2026, 9, tmp_path)

    # A different month is fine.
    other = jobs.submit(2026, 10, tmp_path)
    assert other.month == 10


def test_completed_month_can_be_scraped_again(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        jobs, "run_pipeline", lambda toc_url, output_dir, progress=None: Path(output_dir) / "x.epub"
    )
    first = jobs.submit(2026, 9, tmp_path)
    wait_for(first, "done")
    second = jobs.submit(2026, 9, tmp_path)
    assert second.id != first.id


def test_get_and_all_jobs(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        jobs, "run_pipeline", lambda toc_url, output_dir, progress=None: Path(output_dir) / "x.epub"
    )
    job = jobs.submit(2026, 9, tmp_path)
    wait_for(job, "done")
    assert jobs.get(job.id) is job
    assert jobs.get("nope") is None
    assert [j.id for j in jobs.all_jobs()] == [job.id]

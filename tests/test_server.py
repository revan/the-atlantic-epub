from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from magazine_scraper import jobs, server


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    """A client whose output directory lives in tmp_path."""
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setenv("OUTPUT_DIR", str(output))
    jobs._jobs.clear()
    with TestClient(server.app) as c:
        yield c
    jobs._jobs.clear()


@pytest.fixture
def output(client) -> Path:
    return server.output_dir()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_files_empty(client):
    assert client.get("/files").json() == []


def test_list_files_is_chronological(client, output: Path):
    for name in ("The Atlantic 2026-09.epub", "The Atlantic 2025-01.epub"):
        (output / name).write_bytes(b"PK\x03\x04fake")
    (output / "notes.txt").write_text("ignored")

    body = client.get("/files").json()
    assert [f["name"] for f in body] == [
        "The Atlantic 2025-01.epub",
        "The Atlantic 2026-09.epub",
    ]
    assert body[0]["size_bytes"] == len(b"PK\x03\x04fake")


def test_download_file(client, output: Path):
    (output / "The Atlantic 2026-09.epub").write_bytes(b"PK\x03\x04payload")

    response = client.get("/files/The Atlantic 2026-09.epub")
    assert response.status_code == 200
    assert response.content == b"PK\x03\x04payload"
    assert response.headers["content-type"] == "application/epub+zip"


def test_download_missing_file(client):
    assert client.get("/files/nope.epub").status_code == 404


@pytest.mark.parametrize(
    "filename",
    [
        "../.env",
        "..%2F..%2Fetc%2Fpasswd",
        "../../etc/passwd",
        "subdir/inner.epub",
    ],
)
def test_download_rejects_path_escape(client, output: Path, tmp_path: Path, filename: str):
    """Nothing outside the output directory is reachable."""
    (tmp_path / ".env").write_text("SECRET=1")
    nested = output / "subdir"
    nested.mkdir()
    (nested / "inner.epub").write_bytes(b"nested")

    response = client.get(f"/files/{filename}")
    assert response.status_code == 404
    assert b"SECRET" not in response.content


def test_download_rejects_non_epub(client, output: Path):
    (output / "notes.txt").write_text("plain")
    assert client.get("/files/notes.txt").status_code == 404


def test_scrape_queues_a_job(client, monkeypatch):
    monkeypatch.setattr(
        jobs, "run_pipeline", lambda toc_url, output_dir, progress=None: Path(output_dir) / "x.epub"
    )
    response = client.post("/scrape", json={"year": 2026, "month": 9})
    assert response.status_code == 202

    body = response.json()
    assert body["toc_url"] == "https://www.theatlantic.com/magazine/toc/2026/09/"
    assert body["year"] == 2026

    assert client.get(f"/jobs/{body['id']}").status_code == 200
    assert len(client.get("/jobs").json()) == 1


@pytest.mark.parametrize(
    "payload",
    [{"year": 2026, "month": 13}, {"year": 2026, "month": 0}, {"year": 2026}, {"month": 9}],
)
def test_scrape_validates_month(client, payload: dict):
    assert client.post("/scrape", json=payload).status_code == 422


def test_scrape_rejects_duplicate_issue(client, monkeypatch):
    import time

    def slow(toc_url, output_dir, progress=None):
        time.sleep(0.2)
        return Path(output_dir) / "x.epub"

    monkeypatch.setattr(jobs, "run_pipeline", slow)

    assert client.post("/scrape", json={"year": 2026, "month": 9}).status_code == 202
    assert client.post("/scrape", json={"year": 2026, "month": 9}).status_code == 409


def test_unknown_job(client):
    assert client.get("/jobs/deadbeef").status_code == 404

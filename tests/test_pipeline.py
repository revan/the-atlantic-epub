from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from magazine_scraper.pipeline import month_to_toc_url, run_pipeline, url_to_filename


def test_run_pipeline_produces_output(tmp_path: Path):
    mock_context = MagicMock()
    mock_ctx_manager = MagicMock()
    mock_ctx_manager.__enter__ = MagicMock(return_value=mock_context)
    mock_ctx_manager.__exit__ = MagicMock(return_value=False)
    with (
        patch("magazine_scraper.pipeline.browser_context", return_value=mock_ctx_manager),
        patch("magazine_scraper.pipeline.time.sleep"),
    ):
        result = run_pipeline("https://example.com/issue-1", tmp_path)
        assert result.exists()
        assert result.parent == tmp_path
        assert result.suffix == ".epub"
    mock_ctx_manager.__exit__.assert_called_once()


@pytest.mark.parametrize(
    ("toc_url", "expected"),
    [
        ("https://www.theatlantic.com/magazine/toc/2026/04/", "The Atlantic 2026-04.epub"),
        ("https://www.theatlantic.com/magazine/toc/2024/03/", "The Atlantic 2024-03.epub"),
        ("https://www.theatlantic.com/magazine/toc/2025/12/", "The Atlantic 2025-12.epub"),
        ("https://www.theatlantic.com/magazine/toc/2025/12", "The Atlantic 2025-12.epub"),
        ("https://example.com/no-date", "The Atlantic.epub"),
    ],
)
def test_url_to_filename(toc_url: str, expected: str) -> None:
    assert url_to_filename(toc_url) == expected


@pytest.mark.parametrize(
    ("year", "month", "expected"),
    [
        (2026, 9, "https://www.theatlantic.com/magazine/toc/2026/09/"),
        (2026, 12, "https://www.theatlantic.com/magazine/toc/2026/12/"),
        (1857, 11, "https://www.theatlantic.com/magazine/toc/1857/11/"),
    ],
)
def test_month_to_toc_url(year: int, month: int, expected: str):
    assert month_to_toc_url(year, month) == expected


def test_month_to_toc_url_round_trips_to_filename():
    """The URL a month builds must feed url_to_filename's YYYY-MM scheme."""
    assert url_to_filename(month_to_toc_url(2026, 9)) == "The Atlantic 2026-09.epub"


def test_run_pipeline_reports_progress(tmp_path: Path):
    mock_ctx_manager = MagicMock()
    mock_ctx_manager.__enter__ = MagicMock(return_value=MagicMock())
    mock_ctx_manager.__exit__ = MagicMock(return_value=False)
    steps: list[tuple[str, int, int]] = []
    with (
        patch("magazine_scraper.pipeline.browser_context", return_value=mock_ctx_manager),
        patch("magazine_scraper.pipeline.time.sleep"),
    ):
        run_pipeline(
            "https://example.com/issue-1",
            tmp_path,
            progress=lambda step, done, total: steps.append((step, done, total)),
        )

    assert [s[0] for s in steps][:1] == ["scraping table of contents"]
    assert steps[-1][0] == "building EPUB"

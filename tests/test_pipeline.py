from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from magazine_scraper.pipeline import run_pipeline, url_to_filename


def test_run_pipeline_produces_output(tmp_path: Path):
    mock_context = MagicMock()
    with (
        patch("magazine_scraper.pipeline.login", return_value=mock_context),
        patch("magazine_scraper.pipeline.time.sleep"),
    ):
        result = run_pipeline("https://example.com/issue-1", tmp_path)
        assert result.exists()
        assert result.parent == tmp_path
        assert result.suffix == ".epub"
    mock_context.close.assert_called_once()


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

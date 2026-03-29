from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from magazine_scraper.pipeline import run_pipeline, title_to_filename


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
    ("title", "expected"),
    [
        ("September 2099", "September_2099.epub"),
        ("The Atlantic — March 2024", "The_Atlantic_March_2024.epub"),
        ("Hello  World", "Hello_World.epub"),
        ("Special! Ch@rs & More", "Special_Ch_rs_More.epub"),
        ("  Leading/Trailing Spaces  ", "Leading_Trailing_Spaces.epub"),
        ("", "magazine.epub"),
        ("!!!???", "magazine.epub"),
    ],
)
def test_title_to_filename(title: str, expected: str) -> None:
    assert title_to_filename(title) == expected

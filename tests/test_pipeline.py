from pathlib import Path
from unittest.mock import MagicMock, patch

from magazine_scraper.pipeline import run_pipeline


def test_run_pipeline_produces_output(tmp_path: Path):
    mock_context = MagicMock()
    with (
        patch("magazine_scraper.pipeline.login", return_value=mock_context),
        patch("magazine_scraper.pipeline.time.sleep"),
    ):
        output = tmp_path / "output.epub"
        result = run_pipeline("https://example.com/issue-1", output)
        assert result.exists()
    mock_context.close.assert_called_once()

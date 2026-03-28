from pathlib import Path

from magazine_scraper.pipeline import run_pipeline


def test_run_pipeline_produces_output(tmp_path: Path):
    output = tmp_path / "output.epub"
    result = run_pipeline("https://example.com/issue-1", output)
    assert result.exists()

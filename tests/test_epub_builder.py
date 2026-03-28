from pathlib import Path

from magazine_scraper.epub_builder import build_epub
from magazine_scraper.models import Article, TableOfContents


def test_build_epub_creates_file(tmp_path: Path):
    toc = TableOfContents(
        title="Test Issue",
        articles=[
            Article(title="Article 1", url="https://example.com/1", content="<p>Content</p>"),
        ],
    )
    output = tmp_path / "test.epub"
    result = build_epub(toc, output)
    assert result.exists()
    assert "Test Issue" in result.read_text()

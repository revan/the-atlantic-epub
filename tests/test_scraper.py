from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from magazine_scraper.models import Article
from magazine_scraper.scraper import scrape_article, scrape_toc

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def toc_html() -> str:
    return (FIXTURES_DIR / "toc_sample.html").read_text()


@pytest.fixture()
def mock_playwright(toc_html: str) -> Generator[MagicMock]:
    """Build a mock sync_playwright context that serves fixture HTML."""
    from playwright.sync_api import sync_playwright

    # Real Playwright page with fixture content (no network)
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.set_content(toc_html)

    # Wrap the real page so goto is a no-op (content is already loaded)
    mock_page = MagicMock(wraps=page)
    mock_page.goto = MagicMock()

    # Mock that returns this pre-loaded page
    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_browser.close = browser.close
    mock_pw.chromium.launch.return_value = mock_browser
    mock_pw.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = MagicMock(return_value=False)

    yield mock_pw

    browser.close()
    pw.stop()


def test_scrape_toc_extracts_title_and_articles(mock_playwright: MagicMock) -> None:
    with patch("magazine_scraper.scraper.sync_playwright", return_value=mock_playwright):
        toc = scrape_toc("https://www.example.com/magazine/toc/2099/09/")

    assert toc.title == "September 2099"
    assert len(toc.articles) == 3

    assert toc.articles[0].title == "The Rise of Quantum Gardening"
    assert toc.articles[1].title == "A Brief History of Invisible Bridges"
    assert toc.articles[2].title == "The Last Library on Mars"

    for a in toc.articles:
        assert "/magazine/" in a.url
        assert "/magazine/toc" not in a.url
        assert "/games/" not in a.url


def test_scrape_toc_deduplicates_links(mock_playwright: MagicMock) -> None:
    """The fixture has a duplicate link for the first article; it should appear only once."""
    with patch("magazine_scraper.scraper.sync_playwright", return_value=mock_playwright):
        toc = scrape_toc("https://www.example.com/magazine/toc/2099/09/")

    urls = [a.url for a in toc.articles]
    assert len(urls) == len(set(urls))


def test_scrape_toc_normalizes_relative_urls(mock_playwright: MagicMock) -> None:
    """Relative hrefs should be expanded to absolute URLs."""
    with patch("magazine_scraper.scraper.sync_playwright", return_value=mock_playwright):
        toc = scrape_toc("https://www.example.com/magazine/toc/2099/09/")

    last = toc.articles[-1]
    assert last.title == "The Last Library on Mars"
    assert last.url.startswith("https://")
    assert "/magazine/2099/09/the-last-library-on-mars/333333/" in last.url


def test_scrape_article_fills_content() -> None:
    article = Article(title="Test Article", url="https://example.com/test")
    scrape_article(article)
    assert article.content is not None
    assert article.content != ""
    assert "Test Article" in article.content

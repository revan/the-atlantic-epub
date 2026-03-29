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


def test_scrape_toc_extracts_cover_image_url(mock_playwright: MagicMock) -> None:
    """The fixture has a cover <img> with class IssueDescription_cover__*."""
    with patch("magazine_scraper.scraper.sync_playwright", return_value=mock_playwright):
        toc = scrape_toc("https://www.example.com/magazine/toc/2099/09/")

    assert toc.cover_image_url == "https://cdn.example.com/covers/2099-09-cover.jpg"


def test_scrape_toc_cover_image_url_none_when_missing() -> None:
    """When there is no cover image element, cover_image_url should be None."""
    from playwright.sync_api import sync_playwright

    html = """
    <html><body>
      <h1>No Cover Issue</h1>
      <a href="/magazine/2099/09/article/111/">An Article</a>
    </body></html>
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.set_content(html)

    mock_page = MagicMock(wraps=page)
    mock_page.goto = MagicMock()

    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_browser.close = browser.close
    mock_pw.chromium.launch.return_value = mock_browser
    mock_pw.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = MagicMock(return_value=False)

    try:
        with patch("magazine_scraper.scraper.sync_playwright", return_value=mock_pw):
            toc = scrape_toc("https://www.example.com/magazine/toc/2099/09/")
        assert toc.cover_image_url is None
    finally:
        browser.close()
        pw.stop()


def test_scrape_toc_normalizes_relative_urls(mock_playwright: MagicMock) -> None:
    """Relative hrefs should be expanded to absolute URLs."""
    with patch("magazine_scraper.scraper.sync_playwright", return_value=mock_playwright):
        toc = scrape_toc("https://www.example.com/magazine/toc/2099/09/")

    last = toc.articles[-1]
    assert last.title == "The Last Library on Mars"
    assert last.url.startswith("https://")
    assert "/magazine/2099/09/the-last-library-on-mars/333333/" in last.url


@pytest.fixture()
def article_html() -> str:
    return (FIXTURES_DIR / "article_sample.html").read_text()


@pytest.fixture()
def mock_article_browser(article_html: str) -> Generator[MagicMock]:
    """Build a mock BrowserContext whose pages serve the article fixture HTML."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    real_browser = pw.chromium.launch()
    page = real_browser.new_page()
    page.set_content(article_html)

    # Wrap so goto is a no-op (content already loaded) and close is harmless
    mock_page = MagicMock(wraps=page)
    mock_page.goto = MagicMock()
    mock_page.close = MagicMock()

    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    yield mock_browser

    real_browser.close()
    pw.stop()


@pytest.fixture()
def scraped_article(mock_article_browser: MagicMock) -> Article:
    """Run scrape_article with the fixture and return the populated Article."""
    article = Article(
        title="The Quantum Gardening Revolution",
        url="https://example.com/magazine/2099/09/quantum-gardening/111111/",
    )
    scrape_article(article, mock_article_browser)
    return article


def test_scrape_article_extracts_body_paragraphs(scraped_article: Article) -> None:
    """Content should include the real article paragraphs."""
    assert scraped_article.content is not None
    assert scraped_article.content != ""
    assert "group of Martian settlers" in scraped_article.content
    assert "quantum-entangled seeds" in scraped_article.content
    assert "The debate would rage for decades to come." in scraped_article.content


def test_scrape_article_strips_hyperlinks(scraped_article: Article) -> None:
    """Hyperlink tags should be removed but their text content kept."""
    assert scraped_article.content is not None
    # The link text is preserved
    assert "Nova Terra University" in scraped_article.content
    # The <a> tag and href are gone
    assert "<a " not in scraped_article.content
    assert "example.com/university" not in scraped_article.content


def test_scrape_article_omits_images(scraped_article: Article) -> None:
    """Inline image blocks should not appear in the output."""
    assert scraped_article.content is not None
    assert "quantum-garden.jpg" not in scraped_article.content
    assert "quantum garden on Mars" not in scraped_article.content
    assert "<img" not in scraped_article.content


def test_scrape_article_skips_boilerplate(scraped_article: Article) -> None:
    """Newsletter promo and print-edition credit should be excluded."""
    assert scraped_article.content is not None
    assert "Galactic Digest newsletter" not in scraped_article.content
    assert "Seeds of Tomorrow" not in scraped_article.content
    assert "print edition" not in scraped_article.content


def test_scrape_article_preserves_emphasis(scraped_article: Article) -> None:
    """<em> tags for italics should remain in the output HTML."""
    assert scraped_article.content is not None
    assert "<em>" in scraped_article.content
    assert "The Martian Agricultural" in scraped_article.content


@pytest.fixture()
def multi_hr_html() -> str:
    return (FIXTURES_DIR / "article_multi_hr.html").read_text()


@pytest.fixture()
def mock_multi_hr_browser(multi_hr_html: str) -> Generator[MagicMock]:
    """Build a mock BrowserContext whose pages serve the multi-<hr> fixture."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    real_browser = pw.chromium.launch()
    page = real_browser.new_page()
    page.set_content(multi_hr_html)

    mock_page = MagicMock(wraps=page)
    mock_page.goto = MagicMock()
    mock_page.close = MagicMock()

    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    yield mock_browser

    real_browser.close()
    pw.stop()


@pytest.fixture()
def scraped_multi_hr_article(mock_multi_hr_browser: MagicMock) -> Article:
    """Run scrape_article on the multi-<hr> fixture."""
    article = Article(
        title="Multi-Section Article",
        url="https://example.com/magazine/2099/09/multi-section/999999/",
    )
    scrape_article(article, mock_multi_hr_browser)
    return article


def test_scrape_article_with_multiple_hrs(scraped_multi_hr_article: Article) -> None:
    """Content after mid-article <hr> dividers must be preserved."""
    assert scraped_multi_hr_article.content is not None
    # First section paragraph
    assert "ambassador to Italy" in scraped_multi_hr_article.content
    # Second section paragraph (was previously truncated)
    assert (
        "But here she was in a Senate hearing room in October" in scraped_multi_hr_article.content
    )
    # Third paragraph
    assert "captures all sections of long-form articles" in scraped_multi_hr_article.content


def test_scrape_article_multi_hr_skips_boilerplate(
    scraped_multi_hr_article: Article,
) -> None:
    """Newsletter boilerplate and print-edition credit should still be excluded."""
    assert scraped_multi_hr_article.content is not None
    assert "One Story to Read Today" not in scraped_multi_hr_article.content
    assert "print edition" not in scraped_multi_hr_article.content
    assert "Sections Test" not in scraped_multi_hr_article.content

from magazine_scraper.models import Article, TableOfContents
from magazine_scraper.scraper import scrape_article, scrape_toc


def test_scrape_toc_returns_table_of_contents():
    toc = scrape_toc("https://example.com/issue-1")
    assert isinstance(toc, TableOfContents)
    assert len(toc.articles) > 0
    assert all(isinstance(a, Article) for a in toc.articles)


def test_scrape_article_fills_content():
    article = Article(title="Test Article", url="https://example.com/test")
    scrape_article(article)
    assert article.content is not None
    assert article.content != ""
    assert "Test Article" in article.content

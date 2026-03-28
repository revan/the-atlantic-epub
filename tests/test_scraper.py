from magazine_scraper.models import Article, TableOfContents
from magazine_scraper.scraper import scrape_article, scrape_toc


async def test_scrape_toc_returns_table_of_contents():
    toc = await scrape_toc("https://example.com/issue-1")
    assert isinstance(toc, TableOfContents)
    assert len(toc.articles) > 0
    assert all(isinstance(a, Article) for a in toc.articles)


async def test_scrape_article_fills_content():
    article = Article(title="Test Article", url="https://example.com/test", content="")
    result = await scrape_article(article)
    assert isinstance(result, Article)
    assert result.content != ""
    assert "Test Article" in result.content

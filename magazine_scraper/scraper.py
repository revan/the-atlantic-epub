from magazine_scraper.models import Article, TableOfContents


def scrape_toc(url: str) -> TableOfContents:
    """Scrape the Table of Contents page to extract article URLs."""
    # TODO: implement with playwright
    return TableOfContents(
        title="Placeholder Issue",
        articles=[
            Article(title="Placeholder Article 1", url="https://example.com/article-1"),
            Article(title="Placeholder Article 2", url="https://example.com/article-2"),
        ],
    )


def scrape_article(article: Article) -> None:
    """Scrape an individual article page to get its content."""
    # TODO: implement with playwright
    article.content = "<p>Placeholder content for {}</p>".format(article.title)

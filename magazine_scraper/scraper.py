from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from magazine_scraper.models import Article, TableOfContents


def scrape_toc(url: str) -> TableOfContents:
    """Scrape the Table of Contents page to extract article URLs."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # Extract issue title from the <h1>
        h1 = page.query_selector("h1")
        title = (h1.text_content() or "").strip() if h1 else "Unknown Issue"

        # Extract article links: include /magazine/ paths, exclude /magazine/toc and /games/
        link_elements = page.query_selector_all('a[href*="/magazine/"]')
        seen: set[str] = set()
        articles: list[Article] = []
        for link in link_elements:
            href = link.get_attribute("href") or ""
            parsed = urlparse(href)
            path = parsed.path

            # Filter: must start with /magazine/, must not be /magazine/toc*,
            # must not be bare /magazine/ or /magazine/backissues/
            if not path.startswith("/magazine/"):
                continue
            if path.startswith("/magazine/toc"):
                continue
            if path in ("/magazine/", "/magazine/backissues/"):
                continue

            # Normalize to absolute URL
            if href.startswith("/"):
                href = f"https://www.theatlantic.com{href}"

            text = (link.text_content() or "").strip()
            if not text:
                continue

            if href in seen:
                continue
            seen.add(href)

            articles.append(Article(title=text, url=href))

        browser.close()

    return TableOfContents(title=title, articles=articles)


def scrape_article(article: Article) -> None:
    """Scrape an individual article page to get its content."""
    # TODO: implement with playwright
    article.content = "<p>Placeholder content for {}</p>".format(article.title)

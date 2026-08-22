from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import BrowserContext, sync_playwright

from magazine_scraper.models import Article, TableOfContents


def scrape_toc(url: str) -> TableOfContents:
    """Scrape the Table of Contents page to extract article URLs."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        # Extract issue title from the <h1>
        h1 = page.query_selector("h1")
        raw_title = (h1.text_content() or "").strip() if h1 else "Unknown Issue"
        title = f"The Atlantic {raw_title}" if raw_title != "Unknown Issue" else raw_title

        # Extract cover image URL (the image beside "In This Issue")
        cover_img = page.query_selector("img[class*='IssueDescription_cover']")
        cover_image_url = cover_img.get_attribute("src") if cover_img else None

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

    return TableOfContents(title=title, articles=articles, cover_image_url=cover_image_url)


def scrape_article(article: Article, browser: BrowserContext) -> None:
    """Scrape an individual article page to get its content."""
    page = browser.new_page()
    try:
        page.goto(article.url, wait_until="domcontentloaded")

        html = page.content()
    finally:
        page.close()

    soup = BeautifulSoup(html, "lxml")

    # Extract subtitle from the article header
    desc_el = soup.select_one('div[data-flatplan-description="true"] p')
    if desc_el:
        article.subtitle = desc_el.get_text(strip=True)

    # Extract author from the article header
    author_el = soup.select_one('a[data-flatplan-author-link="true"]')
    if author_el:
        article.author = author_el.get_text(strip=True)

    body = soup.select_one('section[data-flatplan-body="true"]')
    if body is None:
        article.content = ""
        return

    # Remove elements before we iterate: images, promo modules, and the <hr>
    # separator plus everything after it.
    for img_div in body.select('div[data-flatplan-inline_image="true"]'):
        img_div.decompose()
    for promo in body.select('div[data-flatplan-ignore="true"]'):
        promo.decompose()

    # Remove everything from the last <hr> separator onward (print-edition credit,
    # etc.).  Earlier <hr> elements are mid-article section dividers and must be kept.
    hrs = body.select("hr")
    hr = hrs[-1] if hrs else None
    if hr:
        for sibling in list(hr.find_next_siblings()):
            if isinstance(sibling, Tag):
                sibling.decompose()
        hr.decompose()

    # Collect content paragraphs, skipping boilerplate (paragraphs with <small>)
    paragraphs: list[Tag] = []
    for p in body.select('p[data-flatplan-paragraph="true"]'):
        if p.find("small"):
            continue
        paragraphs.append(p)

    # Strip hyperlinks: unwrap <a> tags so their text remains inline
    for p in paragraphs:
        for a_tag in p.select("a"):
            a_tag.unwrap()

    article.content = "\n".join(str(p) for p in paragraphs)

import time
from pathlib import Path

from magazine_scraper.auth import login
from magazine_scraper.epub_builder import build_epub
from magazine_scraper.scraper import scrape_article, scrape_toc
from magazine_scraper.writer import write_epub


def run_pipeline(toc_url: str, output_path: Path) -> Path:
    """Run the full scraping pipeline."""
    # Step 1: Scrape table of contents
    toc = scrape_toc(toc_url)
    time.sleep(1)

    # Step 2: Log in
    browser = login()

    # Step 3: Scrape each article
    try:
        for a in toc.articles:
            scrape_article(a, browser)
            time.sleep(1)
    finally:
        browser.close()

    # Step 4: Build EPUB
    epub_bytes = build_epub(toc)

    # Step 5: Write to disk
    return write_epub(epub_bytes, output_path)


def main() -> None:
    import sys

    toc_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/magazine/issue-1"
    output = run_pipeline(toc_url, Path("output/magazine.epub"))
    print(f"EPUB written to {output}")


if __name__ == "__main__":
    main()

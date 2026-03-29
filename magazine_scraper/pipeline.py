import logging
import time
from pathlib import Path

from magazine_scraper.auth import login
from magazine_scraper.epub_builder import build_epub
from magazine_scraper.scraper import scrape_article, scrape_toc
from magazine_scraper.writer import write_epub

logger = logging.getLogger(__name__)


def run_pipeline(toc_url: str, output_path: Path) -> Path:
    """Run the full scraping pipeline."""
    logger.info("Starting pipeline for %s", toc_url)

    # Step 1: Scrape table of contents
    logger.info("Scraping table of contents from %s", toc_url)
    toc = scrape_toc(toc_url)
    logger.info("Found %d articles in '%s'", len(toc.articles), toc.title)
    time.sleep(1)

    # Step 2: Log in
    logger.info("Logging in to The Atlantic")
    browser = login()
    logger.info("Login successful")

    # Step 3: Scrape each article
    total = len(toc.articles)
    try:
        for i, a in enumerate(toc.articles, start=1):
            logger.info("Scraping article %d/%d: %s", i, total, a.title)
            scrape_article(a, browser)
            time.sleep(1)
    finally:
        browser.close()
        logger.info("Browser closed")

    logger.info("All articles scraped")

    # Step 4: Build EPUB
    logger.info("Building EPUB")
    epub_bytes = build_epub(toc)
    logger.info("EPUB built (%d bytes)", len(epub_bytes))

    # Step 5: Write to disk
    logger.info("Writing EPUB to %s", output_path)
    result = write_epub(epub_bytes, output_path)
    logger.info("Pipeline complete — EPUB written to %s", result)
    return result


def main() -> None:
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    toc_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/magazine/issue-1"
    output = run_pipeline(toc_url, Path("output/magazine.epub"))
    logger.info("Done — EPUB written to %s", output)


if __name__ == "__main__":
    main()

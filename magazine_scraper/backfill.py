"""Backfill script that fetches the Atlantic magazine sitemap and runs the pipeline for every issue."""

import logging
import time
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree.ElementTree import fromstring

from magazine_scraper.pipeline import run_pipeline

logger = logging.getLogger(__name__)

SITEMAP_URL = "https://www.theatlantic.com/sitemaps/magazine-issues.xml"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def fetch_issue_urls(sitemap_url: str) -> list[str]:
    """Download the sitemap XML and return all <loc> URLs."""
    logger.info("Fetching sitemap from %s", sitemap_url)
    request = Request(sitemap_url, headers={"User-Agent": "Mozilla/5.0"})
    data: bytes = urlopen(request).read()  # noqa: S310
    time.sleep(1)  # rate-limit

    root = fromstring(data)  # noqa: S314
    urls = [loc.text for loc in root.findall("sm:url/sm:loc", SITEMAP_NS) if loc.text]
    logger.info("Found %d issue URLs in sitemap", len(urls))
    return urls


def backfill(output_dir: Path) -> None:
    """Run the pipeline for every issue in the sitemap."""
    urls = fetch_issue_urls(SITEMAP_URL)
    total = len(urls)
    successes = 0
    failures = 0
    failed_urls: list[str] = []

    for i, url in enumerate(urls, start=1):
        logger.info("Processing %d/%d: %s", i, total, url)
        try:
            run_pipeline(url, output_dir)
            successes += 1
            logger.info("Success %d/%d: %s", i, total, url)
        except Exception:
            failures += 1
            failed_urls.append(url)
            logger.exception("Error %d/%d: %s", i, total, url)

        if i < total:
            logger.info("Sleeping 10 seconds before next issue…")
            time.sleep(10)

    logger.info("=" * 60)
    logger.info(
        "Backfill complete: %d succeeded, %d failed out of %d total", successes, failures, total
    )
    if failed_urls:
        logger.info("Failed URLs:")
        for url in failed_urls:
            logger.info("  %s", url)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    backfill(Path("output"))


if __name__ == "__main__":
    main()

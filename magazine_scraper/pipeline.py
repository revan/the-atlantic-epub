import logging
import re
import time
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

from magazine_scraper.auth import browser_context
from magazine_scraper.epub_builder import build_epub
from magazine_scraper.scraper import scrape_article, scrape_toc
from magazine_scraper.writer import write_epub

logger = logging.getLogger(__name__)

# Reports pipeline progress as (step, done, total); ``total`` is 0 for
# steps that are not per-article.
ProgressCallback = Callable[[str, int, int], None]


def month_to_toc_url(year: int, month: int) -> str:
    """Build the TOC URL for a magazine issue.

    Example: (2026, 9) -> "https://www.theatlantic.com/magazine/toc/2026/09/"
    """
    return f"https://www.theatlantic.com/magazine/toc/{year}/{month:02d}/"


def url_to_filename(toc_url: str) -> str:
    """Extract year-month from a TOC URL and return a sortable filename.

    Example: "https://www.theatlantic.com/magazine/toc/2026/04/" -> "The Atlantic 2026-04.epub"
    """
    match = re.search(r"/(\d{4})/(\d{2})/?", toc_url)
    if not match:
        return "The Atlantic.epub"
    year, month = match.group(1), match.group(2)
    return f"The Atlantic {year}-{month}.epub"


def convert_to_baseline_jpeg(image_data: bytes) -> bytes:
    """Convert any image to baseline (non-progressive) JPEG bytes."""
    img = Image.open(BytesIO(image_data))
    output = BytesIO()
    img.save(output, format="JPEG", quality=85, progressive=False, optimize=False)
    return output.getvalue()


def download_cover_image(url: str) -> bytes:
    """Download the cover image and return it as baseline JPEG bytes."""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data: bytes = urlopen(request).read()  # noqa: S310
    time.sleep(1)  # rate-limit
    return convert_to_baseline_jpeg(data)


def run_pipeline(toc_url: str, output_dir: Path, progress: ProgressCallback | None = None) -> Path:
    """Run the full scraping pipeline."""
    logger.info("Starting pipeline for %s", toc_url)

    def report(step: str, done: int = 0, total: int = 0) -> None:
        if progress is not None:
            progress(step, done, total)

    report("scraping table of contents")

    # Step 1: Scrape table of contents
    logger.info("Scraping table of contents from %s", toc_url)
    toc = scrape_toc(toc_url)
    logger.info("Found %d articles in '%s'", len(toc.articles), toc.title)
    time.sleep(1)

    # Step 2: Download cover image
    cover_image: bytes | None = None
    if toc.cover_image_url:
        report("downloading cover image")
        logger.info("Downloading cover image from %s", toc.cover_image_url)
        cover_image = download_cover_image(toc.cover_image_url)
        logger.info("Cover image downloaded (%d bytes)", len(cover_image))

    # Step 3: Scrape each article
    logger.info("Opening browser context")
    with browser_context() as context:
        total = len(toc.articles)
        report("scraping articles", 0, total)
        for i, a in enumerate(toc.articles, start=1):
            logger.info("Scraping article %d/%d: %s", i, total, a.title)
            report("scraping articles", i, total)
            scrape_article(a, context)
            time.sleep(1)

    logger.info("All articles scraped")

    # Step 4: Build EPUB
    logger.info("Building EPUB")
    report("building EPUB")
    epub_bytes = build_epub(toc, cover_image=cover_image)
    logger.info("EPUB built (%d bytes)", len(epub_bytes))

    # Step 5: Write to disk — filename derived from the TOC URL date
    output_path = output_dir / url_to_filename(toc_url)
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
    output = run_pipeline(toc_url, Path("output"))
    logger.info("Done — EPUB written to %s", output)


if __name__ == "__main__":
    main()

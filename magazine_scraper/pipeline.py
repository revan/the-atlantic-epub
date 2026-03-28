import asyncio
from pathlib import Path

from magazine_scraper.epub_builder import build_epub
from magazine_scraper.scraper import scrape_article, scrape_toc


async def run_pipeline(toc_url: str, output_path: Path) -> Path:
    """Run the full scraping pipeline."""
    # Step 1: Scrape table of contents
    toc = await scrape_toc(toc_url)

    # Step 2: Scrape each article
    toc.articles = [await scrape_article(a) for a in toc.articles]

    # Step 3: Build EPUB
    return build_epub(toc, output_path)


def main() -> None:
    import sys

    toc_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/magazine/issue-1"
    output = asyncio.run(run_pipeline(toc_url, Path("output/magazine.epub")))
    print(f"EPUB written to {output}")


if __name__ == "__main__":
    main()

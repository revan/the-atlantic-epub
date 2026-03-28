from pathlib import Path

from magazine_scraper.models import TableOfContents


def build_epub(toc: TableOfContents, output_path: Path) -> Path:
    """Assemble scraped articles into an EPUB file."""
    # TODO: implement with ebooklib
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"PLACEHOLDER EPUB: {toc.title} ({len(toc.articles)} articles)")
    return output_path

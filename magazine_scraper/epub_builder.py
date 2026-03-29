import os
import tempfile
import uuid

from ebooklib import epub

from magazine_scraper.models import TableOfContents


def build_epub(toc: TableOfContents, cover_image: bytes | None = None) -> bytes:
    """Assemble scraped articles into an in-memory EPUB file."""
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(toc.title)
    book.add_author("The Atlantic")
    book.set_language("en")

    if cover_image is not None:
        book.set_cover("cover.jpg", cover_image)

    chapters: list[epub.EpubHtml] = []
    for i, article in enumerate(toc.articles):
        ch = epub.EpubHtml(title=article.title, file_name=f"article_{i}.xhtml", lang="en")
        subtitle_html = f"<h2>{article.subtitle}</h2>" if article.subtitle else ""
        author_html = f"<p><em>{article.author}</em></p>" if article.author else ""
        ch.content = f"<h1>{article.title}</h1>{subtitle_html}{author_html}{article.content or ''}"
        book.add_item(ch)
        chapters.append(ch)

    book.toc = chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    # ebooklib only supports writing to a file path, so use a temp file
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        epub.write_epub(tmp_path, book)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)

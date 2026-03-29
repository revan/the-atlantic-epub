import io
import zipfile

from magazine_scraper.epub_builder import build_epub
from magazine_scraper.models import Article, TableOfContents


def test_build_epub_returns_valid_epub():
    toc = TableOfContents(
        title="Test Issue",
        articles=[
            Article(title="First", url="http://ex.com/1", content="<p>Hello</p>"),
            Article(title="Second", url="http://ex.com/2", content="<p>World</p>"),
        ],
    )
    data = build_epub(toc)

    assert isinstance(data, bytes)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        # EPUB required: mimetype file first entry
        assert names[0] == "mimetype"
        assert zf.read("mimetype") == b"application/epub+zip"
        # Contains chapter XHTML files
        assert any("article_0" in n for n in names)
        assert any("article_1" in n for n in names)
        # Chapter content is present
        ch0 = zf.read([n for n in names if "article_0" in n][0]).decode()
        assert "First" in ch0
        assert "Hello" in ch0
        # OPF metadata contains the title
        opf = [n for n in names if n.endswith(".opf")][0]
        opf_content = zf.read(opf).decode()
        assert "Test Issue" in opf_content


def test_build_epub_with_cover_image():
    # Minimal valid JPEG: SOI + EOI markers
    fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"
    toc = TableOfContents(
        title="Cover Test",
        articles=[
            Article(title="Art", url="http://ex.com/1", content="<p>Body</p>"),
        ],
    )
    data = build_epub(toc, cover_image=fake_jpeg)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        # The EPUB should contain the cover image file
        cover_entries = [n for n in names if "cover.jpg" in n]
        assert cover_entries, f"No cover.jpg in EPUB; files: {names}"
        # The image bytes should match what we passed in
        assert zf.read(cover_entries[0]) == fake_jpeg
        # OPF should reference the cover
        opf = [n for n in names if n.endswith(".opf")][0]
        opf_content = zf.read(opf).decode()
        assert "cover" in opf_content.lower()


def test_build_epub_without_cover_image():
    """When no cover image is provided, EPUB should not contain cover.jpg."""
    toc = TableOfContents(
        title="No Cover",
        articles=[
            Article(title="Art", url="http://ex.com/1", content="<p>Body</p>"),
        ],
    )
    data = build_epub(toc)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        assert not any("cover.jpg" in n for n in names)


def test_build_epub_no_articles():
    toc = TableOfContents(title="Empty", articles=[])
    data = build_epub(toc)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.read("mimetype") == b"application/epub+zip"


def test_build_epub_includes_subtitle_and_author():
    """Chapter XHTML should include subtitle as <h2> and author in <em>."""
    toc = TableOfContents(
        title="Subtitle Author Test",
        articles=[
            Article(
                title="Featured",
                url="http://ex.com/1",
                content="<p>Body text</p>",
                subtitle="A test subtitle",
                author="Test Author",
            ),
        ],
    )
    data = build_epub(toc)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        ch0 = zf.read([n for n in names if "article_0" in n][0]).decode()
        assert "<h2>A test subtitle</h2>" in ch0
        assert "<em>Test Author</em>" in ch0


def test_build_epub_omits_subtitle_and_author_when_none():
    """When subtitle and author are None, no <h2> or byline should appear."""
    toc = TableOfContents(
        title="No Subtitle Author",
        articles=[
            Article(
                title="Plain",
                url="http://ex.com/1",
                content="<p>Body only</p>",
            ),
        ],
    )
    data = build_epub(toc)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        ch0 = zf.read([n for n in names if "article_0" in n][0]).decode()
        assert "<h2>" not in ch0
        assert "<em>" not in ch0

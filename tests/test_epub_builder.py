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


def test_build_epub_no_articles():
    toc = TableOfContents(title="Empty", articles=[])
    data = build_epub(toc)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.read("mimetype") == b"application/epub+zip"

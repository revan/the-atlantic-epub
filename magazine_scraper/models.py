from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    url: str
    content: str | None = None  # HTML content of the article body
    subtitle: str | None = None
    author: str | None = None


@dataclass
class TableOfContents:
    title: str  # Magazine issue title
    articles: list[Article] = field(default_factory=list)
    cover_image_url: str | None = None

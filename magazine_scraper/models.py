from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    url: str
    content: str  # HTML content of the article body


@dataclass
class TableOfContents:
    title: str  # Magazine issue title
    articles: list[Article] = field(default_factory=list)

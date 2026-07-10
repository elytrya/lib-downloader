from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core.http_utils import PoliteSession, download_bytes
from core.models import BookInfo, ChapterContent, ChapterInfo


class BaseProvider(ABC):
    domains: List[str] = []
    session: Optional[PoliteSession] = None

    @classmethod
    def supports(cls, url: str) -> bool:
        return any(domain in url for domain in cls.domains)

    @abstractmethod
    def resolve_book(self, url: str) -> BookInfo:
        raise NotImplementedError

    @abstractmethod
    def list_chapters(self, book: BookInfo) -> List[ChapterInfo]:
        raise NotImplementedError

    @abstractmethod
    def fetch_chapter(self, book: BookInfo, chapter: ChapterInfo) -> ChapterContent:
        raise NotImplementedError

    def download_page(self, url: str) -> Tuple[bytes, str]:
        return download_bytes(url)

"""
базовый класс провайдера. чтобы добавить поддержку нового сайта,
нужно создать в папке providers/ новый файл с классом-наследником
BaseProvider и зарегистрировать его в providers/registry.py.
"""

from abc import ABC, abstractmethod
from typing import List

from core.models import BookInfo, ChapterContent, ChapterInfo


class BaseProvider(ABC):
    #: домены (или их части), которые обслуживает провайдер
    domains: List[str] = []

    @classmethod
    def supports(cls, url: str) -> bool:
        return any(domain in url for domain in cls.domains)

    @abstractmethod
    def resolve_book(self, url: str) -> BookInfo:
        """получить информацию о книге по ссылке на страницу книги."""
        raise NotImplementedError

    @abstractmethod
    def list_chapters(self, book: BookInfo) -> List[ChapterInfo]:
        """получить список всех глав книги (без содержимого)."""
        raise NotImplementedError

    @abstractmethod
    def fetch_chapter(self, book: BookInfo, chapter: ChapterInfo) -> ChapterContent:
        """скачать и вернуть содержимое конкретной главы."""
        raise NotImplementedError

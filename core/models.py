"""
общие модели данных, используемые всеми провайдерами
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChapterInfo:
    """описание одной главы (без содержимого)"""

    id: int
    volume: str
    number: str
    name: str
    branch_id: Optional[int] = None
    index: Optional[int] = None

    @property
    def display_name(self) -> str:
        title = f"Том {self.volume} Глава {self.number}"
        if self.name:
            title += f" — {self.name}"
        return title


@dataclass
class ChapterContent:
    """
    глава со скачанным содержимым.
    для текстовых глав (ранобэ) заполнено html.
    для глав-картинок (манга/манхва) заполнено pages - список ссылок на изображения.
    """

    info: ChapterInfo
    html: str = ""
    pages: List[str] = field(default_factory=list)

    @property
    def is_image_based(self) -> bool:
        return bool(self.pages)


@dataclass
class BookInfo:
    """Метаданные книги/тайтла."""

    slug: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None

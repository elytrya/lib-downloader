from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChapterInfo:
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
class PageImage:
    url: str
    data: Optional[bytes] = None
    media_type: str = "image/jpeg"


@dataclass
class ChapterContent:
    info: ChapterInfo
    html: str = ""
    pages: List[PageImage] = field(default_factory=list)

    @property
    def is_image_based(self) -> bool:
        return bool(self.pages)


@dataclass
class BookInfo:
    slug: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None

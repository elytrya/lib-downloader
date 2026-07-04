"""
провайдер для mangalib.me (mangalib.org)
"""

from typing import List, Optional

from core.http_utils import PoliteSession
from core.models import BookInfo, ChapterContent, ChapterInfo
from providers.cdnlibs_base import CdnlibsBaseProvider

IMAGE_HOST = "https://img3.cdnlibs.org"


class MangalibProvider(CdnlibsBaseProvider):
    domains = ["mangalib.me", "mangalib.org"]
    referer = "https://mangalib.me/"

    def __init__(
        self, session: Optional[PoliteSession] = None, image_host: str = IMAGE_HOST
    ):
        super().__init__(session=session)
        self.image_host = image_host.rstrip("/")

    def _full_image_url(self, raw_url: str) -> str:
        # "//manga/..." -> "/manga/..." -> host + "/manga/..."
        path = raw_url[1:] if raw_url.startswith("//") else raw_url
        if not path.startswith("/"):
            path = "/" + path
        return self.image_host + path

    def fetch_chapter(self, book: BookInfo, chapter: ChapterInfo) -> ChapterContent:
        params = {"number": chapter.number, "volume": chapter.volume}
        if chapter.branch_id:
            params["branch_id"] = chapter.branch_id

        # ИСПРАВЛЕНО: добавлено "manga/" в путь запроса, чтобы не было 404
        data = self._get(f"manga/{book.slug}/chapter", params=params)
        item = data.get("data", {})
        pages = item.get("pages") or []

        image_urls: List[str] = []
        for page in pages:
            raw_url = page.get("url")
            if raw_url:
                image_urls.append(self._full_image_url(raw_url))

        return ChapterContent(info=chapter, pages=image_urls)

from typing import Optional, Tuple

from core.http_utils import PoliteSession, download_bytes
from core.models import BookInfo, ChapterContent, ChapterInfo, PageImage
from providers.cdnlibs_base import CdnlibsBaseProvider

IMAGE_HOST = "https://img3h.hentaicdn.org"
IMAGE_REFERER = "https://hentailib.me/"


class HentailibProvider(CdnlibsBaseProvider):
    domains = ["hentailib.me", "hentailib.org"]
    referer = "https://hentailib.me/"

    def __init__(
        self,
        session: Optional[PoliteSession] = None,
        image_host: str = IMAGE_HOST,
    ):
        super().__init__(session=session)
        self.image_host = image_host.rstrip("/")

    def _full_image_url(self, raw_url: str) -> str:
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            return raw_url
        path = raw_url[1:] if raw_url.startswith("//") else raw_url
        if not path.startswith("/"):
            path = "/" + path
        return self.image_host + path

    def download_page(self, url: str) -> Tuple[bytes, str]:
        return download_bytes(url, headers={"Referer": IMAGE_REFERER})

    def fetch_chapter(self, book: BookInfo, chapter: ChapterInfo) -> ChapterContent:
        params = {"number": chapter.number, "volume": chapter.volume}
        if chapter.branch_id:
            params["branch_id"] = chapter.branch_id

        data = self._get(f"manga/{book.slug}/chapter", params=params)
        item = data.get("data", {})
        pages = [
            PageImage(url=self._full_image_url(p["url"]))
            for p in (item.get("pages") or [])
            if p.get("url")
        ]
        return ChapterContent(info=chapter, pages=pages)

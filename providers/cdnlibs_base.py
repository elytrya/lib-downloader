import re
from typing import List, Optional, Tuple

import requests

from core.auth import load_auth_cookies
from core.base_provider import BaseProvider
from core.http_utils import PoliteSession, download_bytes
from core.models import BookInfo, ChapterInfo

API_BASE_URL = "https://api.cdnlibs.org/api"
IMAGE_REFERER = "https://cdnlibs.org/"


class CdnlibsBaseProvider(BaseProvider):
    referer = "https://mangalib.me/"

    def __init__(self, session: Optional[PoliteSession] = None):
        headers = {"Accept": "application/json", "Referer": self.referer}
        self.session = session or PoliteSession(headers=headers)
        self._apply_auth()

    def _apply_auth(self) -> None:
        auth = load_auth_cookies()
        token = auth.get("mangalib_token")
        if token:
            self.session.headers["Authorization"] = token
        sess = auth.get("mangalib_session")
        if sess:
            self.session.cookies.update({"mangalib_session": sess})

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        resp = self.session.get(f"{API_BASE_URL}/{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    def _extract_slug(self, url: str) -> str:
        match = re.search(r"/(?:ru/)?(?:manga/)?(\d+--[\w\-]+)", url)
        if not match:
            raise ValueError(f"Не удалось найти слаг тайтла в ссылке: {url}")
        return match.group(1)

    def resolve_book(self, url: str) -> BookInfo:
        slug = self._extract_slug(url)
        title, author, cover_url, description = slug, None, None, None

        try:
            data = self._get(f"manga/{slug}")
            item = data.get("data", data)
            title = item.get("rus_name") or item.get("name") or slug
            cover = item.get("cover") or {}
            cover_url = cover.get("default") or cover.get("md")
            description = item.get("summary")
            authors = item.get("authors") or []
            if authors:
                author = ", ".join(a.get("name", "") for a in authors if a.get("name"))
        except requests.RequestException:
            pass

        return BookInfo(
            slug=slug,
            title=title,
            author=author,
            cover_url=cover_url,
            description=description,
        )

    def list_chapters(self, book: BookInfo) -> List[ChapterInfo]:
        data = self._get(f"manga/{book.slug}/chapters")
        chapters = []
        for item in data.get("data", []):
            branches = item.get("branches") or []
            branch_id = None
            if branches:
                branch_id = branches[0].get("branch_id") or branches[0].get("id")
            chapters.append(
                ChapterInfo(
                    id=item.get("id"),
                    volume=str(item.get("volume", "")),
                    number=str(item.get("number", "")),
                    name=item.get("name") or "",
                    branch_id=branch_id,
                    index=item.get("index"),
                )
            )
        chapters.sort(key=lambda c: c.index if c.index is not None else 0)
        return chapters

    def download_page(self, url: str) -> Tuple[bytes, str]:
        return download_bytes(url, headers={"Referer": IMAGE_REFERER})

"""
общая часть для провайдеров, использующих апи cdnlibs.org
достаёт слаг из ссылки, получает инфу о тайтле и список глав -
это одинаково для всех сайтов семейства. Отличается только разбор
содержимого конкретной главы (текст vs картинки) - это делают
дочерние классы в fetch_chapter.
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests

from core.auth import load_auth_cookies
from core.base_provider import BaseProvider
from core.http_utils import PoliteSession
from core.models import BookInfo, ChapterInfo

API_BASE_URL = "https://api.cdnlibs.org/api"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class CdnlibsBaseProvider(BaseProvider):
    referer = "https://mangalib.me/"

    def __init__(self, session: Optional[PoliteSession] = None):
        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = self.referer
        self.session = session or PoliteSession(headers=headers)

        auth_cookies = load_auth_cookies()
        if "mangalib_token" in auth_cookies:
            if hasattr(self.session, "headers"):
                if isinstance(self.session.headers, dict):
                    self.session.headers["Authorization"] = auth_cookies[
                        "mangalib_token"
                    ]
                else:
                    self.session.headers.update(
                        {"Authorization": auth_cookies["mangalib_token"]}
                    )
            elif hasattr(self.session, "session") and hasattr(
                self.session.session, "headers"
            ):
                self.session.session.headers["Authorization"] = auth_cookies[
                    "mangalib_token"
                ]

        if "mangalib_session" in auth_cookies:
            if hasattr(self.session, "session"):
                self.session.session.cookies.update(
                    {"mangalib_session": auth_cookies["mangalib_session"]}
                )
            elif hasattr(self.session, "cookies"):
                self.session.cookies.update(
                    {"mangalib_session": auth_cookies["mangalib_session"]}
                )

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{API_BASE_URL}/{path}"
        resp = self.session.get(url, params=params)
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

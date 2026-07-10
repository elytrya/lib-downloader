from core.content_renderer import render_doc
from core.models import BookInfo, ChapterContent, ChapterInfo
from providers.cdnlibs_base import CdnlibsBaseProvider


class RanobelibProvider(CdnlibsBaseProvider):
    domains = ["ranobelib.me"]
    referer = "https://ranobelib.me/"

    def fetch_chapter(self, book: BookInfo, chapter: ChapterInfo) -> ChapterContent:
        params = {"number": chapter.number, "volume": chapter.volume}
        if chapter.branch_id:
            params["branch_id"] = chapter.branch_id

        data = self._get(f"manga/{book.slug}/chapter", params=params)
        item = data.get("data", {})
        content = item.get("content")
        html = render_doc(content) if content else ""
        return ChapterContent(info=chapter, html=html)

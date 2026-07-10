import os
import re
from typing import List, Optional

from core.base_provider import BaseProvider
from core.http_utils import media_type_to_ext
from core.models import BookInfo, ChapterContent

_IMG_SRC_RE = re.compile(
    r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)\2',
    re.IGNORECASE | re.DOTALL,
)


def _sanitize_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def _download_images_in_html(
    html: str, chapter_dir: str, provider: Optional[BaseProvider]
) -> str:
    images_dir = os.path.join(chapter_dir, "images")
    cache: dict = {}
    counter = {"n": 0}

    def replace(match):
        prefix, quote, src = match.group(1), match.group(2), match.group(3)
        if not src or src.startswith("data:"):
            return match.group(0)
        if not re.match(r"^https?://", src, re.IGNORECASE):
            return match.group(0)

        if src in cache:
            return f"{prefix}{quote}{cache[src]}{quote}"

        counter["n"] += 1
        try:
            if provider is None:
                raise RuntimeError("provider is required for image download")
            data, media_type = provider.download_page(src)
        except Exception as e:
            print(f"      Не удалось скачать картинку {src}: {e}")
            return match.group(0)

        file_name = f"{counter['n']:04d}.{media_type_to_ext(media_type)}"
        os.makedirs(images_dir, exist_ok=True)
        with open(os.path.join(images_dir, file_name), "wb") as f:
            f.write(data)

        local = f"images/{file_name}"
        cache[src] = local
        return f"{prefix}{quote}{local}{quote}"

    return _IMG_SRC_RE.sub(replace, html)


def _wrap_html_document(title: str, body_html: str) -> str:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        "<!doctype html>\n"
        '<html lang="ru">\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        f"<title>{safe_title}</title>\n"
        "<style>\n"
        "body { font-family: serif; line-height: 1.5; max-width: 780px; "
        "margin: 2em auto; padding: 0 1em; }\n"
        "h1, h2, h3 { text-align: center; }\n"
        "img { max-width: 100%; height: auto; display: block; margin: 1em auto; }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        f"<h2>{safe_title}</h2>\n"
        f"{body_html}\n"
        "</body>\n"
        "</html>\n"
    )


def save_chapters_as_folders(
    book: BookInfo,
    chapters: List[ChapterContent],
    output_dir: str,
    provider: Optional[BaseProvider] = None,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    for idx, ch in enumerate(chapters, start=1):
        safe_ch_name = _sanitize_name(ch.info.display_name) or f"chapter-{idx}"
        chapter_dir = os.path.join(output_dir, f"chapter-{idx} - {safe_ch_name}")
        os.makedirs(chapter_dir, exist_ok=True)

        if ch.is_image_based:
            for page_idx, page in enumerate(ch.pages, start=1):
                if not page.data:
                    continue
                ext = media_type_to_ext(page.media_type)
                with open(os.path.join(chapter_dir, f"{page_idx:04d}.{ext}"), "wb") as f:
                    f.write(page.data)
        else:
            html_local = _download_images_in_html(ch.html, chapter_dir, provider)
            with open(os.path.join(chapter_dir, "chapter.html"), "w", encoding="utf-8") as f:
                f.write(_wrap_html_document(ch.info.display_name, html_local))

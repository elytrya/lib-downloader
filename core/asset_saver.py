"""
второй режим вывода - вместо одного epub создаём папку с подпапками
chapter-N. для картиночных глав туда падают сами страницы (манга/манхва),
для текстовых (ранобэ) - chapter.html + подпапка images/ со всеми
картинками, на которые ссылается html.
"""

import mimetypes
import os
import re
from typing import List

import requests

from core.http_utils import PoliteSession
from core.models import BookInfo, ChapterContent

_IMG_SRC_RE = re.compile(
    r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)\2',
    re.IGNORECASE | re.DOTALL,
)

IMG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://cdnlibs.org/",
}


def _guess_media_type(url: str) -> str:
    ctype, _ = mimetypes.guess_type(url)
    return ctype or "image/jpeg"


def _sanitize_name(name: str) -> str:
    # Удаляем символы, которые нельзя использовать в названиях папок
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def _download_images_in_html(
    html: str,
    chapter_dir: str,
) -> str:
    images_dir = os.path.join(chapter_dir, "images")
    cache: dict = {}
    counter = {"n": 0}

    def replace(match: "re.Match[str]") -> str:
        prefix, quote, src = match.group(1), match.group(2), match.group(3)
        if not src or src.startswith("data:"):
            return match.group(0)
        if not re.match(r"^https?://", src, re.IGNORECASE):
            return match.group(0)

        if src in cache:
            return f"{prefix}{quote}{cache[src]}{quote}"

        counter["n"] += 1
        ext = _guess_media_type(src).split("/")[-1]
        file_name = f"{counter['n']:04d}.{ext}"
        file_path = os.path.join(images_dir, file_name)

        try:
            os.makedirs(images_dir, exist_ok=True)
            resp = requests.get(src, headers=IMG_HEADERS, stream=True)
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(1024 * 64):
                    f.write(chunk)
        except Exception as e:
            print(f"      Не удалось скачать картинку {src}: {e}")
            return match.group(0)

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
    session: PoliteSession = None,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    for idx, ch in enumerate(chapters, start=1):
        safe_ch_name = _sanitize_name(ch.info.display_name) or f"chapter-{idx}"
        folder_name = f"chapter-{idx} - {safe_ch_name}"
        chapter_dir = os.path.join(output_dir, folder_name)
        os.makedirs(chapter_dir, exist_ok=True)

        if ch.is_image_based:
            for page_idx, image_url in enumerate(ch.pages, start=1):
                ext = _guess_media_type(image_url).split("/")[-1]
                file_path = os.path.join(chapter_dir, f"{page_idx:04d}.{ext}")
                try:
                    resp = requests.get(image_url, headers=IMG_HEADERS, stream=True)
                    resp.raise_for_status()
                    with open(file_path, "wb") as f:
                        for chunk in resp.iter_content(1024 * 64):
                            f.write(chunk)
                except Exception as e:
                    print(f"    Не удалось скачать страницу {page_idx}: {e}")
                    continue
        else:
            html_local = _download_images_in_html(ch.html, chapter_dir)
            file_path = os.path.join(chapter_dir, "chapter.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(_wrap_html_document(ch.info.display_name, html_local))

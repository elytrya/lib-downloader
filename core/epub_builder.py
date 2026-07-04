"""
сборка EPUB-файла из уже скачанных глав.
поддерживает два вида глав: текстовые (ch.html) и картиночные (ch.pages) -
для манги/манхвы картинки докачиваются и вшиваются прямо в epub.
"""

import uuid
from typing import List

import requests
from ebooklib import epub

from core.http_utils import PoliteSession
from core.models import BookInfo, ChapterContent

_CSS = (
    "body { font-family: serif; line-height: 1.5; }\n"
    "h1, h2, h3 { text-align: center; }\n"
    "div.page { text-align: center; margin: 0; padding: 0; }\n"
    "img { max-width: 100%; height: auto; display: block; margin: 0 auto; }\n"
)

IMG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://cdnlibs.org/",
}


def _get_true_media_type(url: str, resp_headers: dict) -> str:
    content_type = resp_headers.get("Content-Type", "").split(";")[0].strip()
    if content_type.startswith("image/"):
        return content_type

    ext = url.rsplit(".", 1)[-1].lower().split("?")[0]
    _EXT_TO_MEDIA = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    return _EXT_TO_MEDIA.get(ext, "image/jpeg")


def build_epub(
    book: BookInfo,
    chapters: List[ChapterContent],
    output_path: str,
    session: PoliteSession = None,
) -> None:
    book_epub = epub.EpubBook()

    book_epub.set_identifier(str(uuid.uuid4()))
    book_epub.set_title(book.title)
    book_epub.set_language("ru")
    if book.author:
        book_epub.add_author(book.author)
    if book.description:
        book_epub.add_metadata("DC", "description", book.description)

    has_cover = False
    if book.cover_url:
        try:
            # Качаем обложку через чистый requests
            resp = requests.get(
                book.cover_url, timeout=30, headers=IMG_HEADERS, stream=True
            )
            resp.raise_for_status()

            content = b""
            for chunk in resp.iter_content(1024 * 64):
                content += chunk

            media_type = _get_true_media_type(book.cover_url, resp.headers)
            ext = media_type.split("/")[-1].replace("jpeg", "jpg")
            book_epub.set_cover(f"cover.{ext}", content)
            has_cover = True
        except Exception as e:
            print(f"    [!] Не удалось добавить обложку: {e}")

    css_item = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=_CSS,
    )
    book_epub.add_item(css_item)

    epub_chapters = []
    for idx, ch in enumerate(chapters, start=1):
        file_name = f"chapter_{idx:04d}.xhtml"
        html_chapter = epub.EpubHtml(
            title=ch.info.display_name,
            file_name=file_name,
            lang="ru",
        )

        if ch.is_image_based:
            body_parts = []
            for page_idx, image_url in enumerate(ch.pages, start=1):
                try:
                    # Качаем сканы через чистый requests чанками по 64 КБ
                    resp = requests.get(image_url, headers=IMG_HEADERS, stream=True)
                    resp.raise_for_status()

                    content = b""
                    for chunk in resp.iter_content(1024 * 64):
                        content += chunk
                except Exception as e:
                    print(
                        f"    [!] Ошибка скачивания страницы {page_idx} (Глава {idx}): {e}"
                    )
                    continue

                media_type = _get_true_media_type(image_url, resp.headers)

                if "webp" in media_type:
                    try:
                        import io

                        from PIL import Image

                        img = Image.open(io.BytesIO(content))
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        out = io.BytesIO()
                        img.save(out, format="JPEG")
                        content = out.getvalue()
                        media_type = "image/jpeg"
                    except ImportError:
                        pass

                ext = media_type.split("/")[-1].replace("jpeg", "jpg")
                image_file_name = f"images/ch{idx:04d}_p{page_idx:04d}.{ext}"

                image_item = epub.EpubItem(
                    uid=f"img_{idx}_{page_idx}",
                    file_name=image_file_name,
                    media_type=media_type,
                    content=content,
                )
                book_epub.add_item(image_item)

                body_parts.append(
                    f'<div class="page"><img src="{image_file_name}" alt="page_{page_idx}"/></div>'
                )

            html_chapter.content = f"<h2>{ch.info.display_name}</h2>\n" + "\n".join(
                body_parts
            )
        else:
            html_chapter.content = f"<h2>{ch.info.display_name}</h2>\n{ch.html}"

        html_chapter.add_item(css_item)
        book_epub.add_item(html_chapter)
        epub_chapters.append(html_chapter)

    book_epub.toc = epub_chapters
    book_epub.add_item(epub.EpubNcx())
    book_epub.add_item(epub.EpubNav())

    spine = ["cover"] if has_cover else []
    spine += ["nav"] + epub_chapters
    book_epub.spine = spine

    epub.write_epub(output_path, book_epub, {})

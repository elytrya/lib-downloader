import io
import uuid
from typing import List, Tuple

from ebooklib import epub

from core.http_utils import download_bytes, media_type_to_ext
from core.models import BookInfo, ChapterContent

_CSS = (
    "body { font-family: serif; line-height: 1.5; }\n"
    "h1, h2, h3 { text-align: center; }\n"
    "div.page { text-align: center; margin: 0; padding: 0; }\n"
    "img { max-width: 100%; height: auto; display: block; margin: 0 auto; }\n"
)


def _convert_webp_to_jpeg(content: bytes) -> Tuple[bytes, str]:
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG")
        return out.getvalue(), "image/jpeg"
    except Exception:
        return content, "image/webp"


def build_epub(book: BookInfo, chapters: List[ChapterContent], output_path: str) -> None:
    epub_book = epub.EpubBook()
    epub_book.set_identifier(str(uuid.uuid4()))
    epub_book.set_title(book.title)
    epub_book.set_language("ru")
    if book.author:
        epub_book.add_author(book.author)
    if book.description:
        epub_book.add_metadata("DC", "description", book.description)

    has_cover = False
    if book.cover_url:
        try:
            content, media_type = download_bytes(book.cover_url)
            epub_book.set_cover(f"cover.{media_type_to_ext(media_type)}", content)
            has_cover = True
        except Exception as e:
            print(f"    [!] Не удалось добавить обложку: {e}")

    css_item = epub.EpubItem(
        uid="style", file_name="style/main.css", media_type="text/css", content=_CSS
    )
    epub_book.add_item(css_item)

    epub_chapters = []
    for idx, ch in enumerate(chapters, start=1):
        html_chapter = epub.EpubHtml(
            title=ch.info.display_name,
            file_name=f"chapter_{idx:04d}.xhtml",
            lang="ru",
        )

        if ch.is_image_based:
            body_parts = []
            for page_idx, page in enumerate(ch.pages, start=1):
                if not page.data:
                    continue
                content = page.data
                media_type = page.media_type
                if "webp" in media_type:
                    content, media_type = _convert_webp_to_jpeg(content)

                ext = media_type_to_ext(media_type)
                image_file_name = f"images/ch{idx:04d}_p{page_idx:04d}.{ext}"
                epub_book.add_item(
                    epub.EpubItem(
                        uid=f"img_{idx}_{page_idx}",
                        file_name=image_file_name,
                        media_type=media_type,
                        content=content,
                    )
                )
                body_parts.append(
                    f'<div class="page"><img src="{image_file_name}" alt="page_{page_idx}"/></div>'
                )

            html_chapter.content = (
                f"<h2>{ch.info.display_name}</h2>\n" + "\n".join(body_parts)
            )
        else:
            html_chapter.content = f"<h2>{ch.info.display_name}</h2>\n{ch.html}"

        html_chapter.add_item(css_item)
        epub_book.add_item(html_chapter)
        epub_chapters.append(html_chapter)

    epub_book.toc = epub_chapters
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    spine = ["cover"] if has_cover else []
    spine += ["nav"] + epub_chapters
    epub_book.spine = spine

    epub.write_epub(output_path, epub_book, {})

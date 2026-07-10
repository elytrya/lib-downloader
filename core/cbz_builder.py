import re
import zipfile
from typing import List

from core.http_utils import media_type_to_ext
from core.models import BookInfo, ChapterContent


def _sanitize_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def build_cbz(book: BookInfo, chapters: List[ChapterContent], output_path: str) -> None:
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_STORED) as cbz:
        for idx, ch in enumerate(chapters, start=1):
            if not ch.is_image_based:
                continue

            safe_ch_name = _sanitize_name(ch.info.display_name) or f"chapter-{idx}"
            ch_folder = f"{idx:04d} - {safe_ch_name}"

            for page_idx, page in enumerate(ch.pages, start=1):
                if not page.data:
                    continue
                ext = media_type_to_ext(page.media_type)
                cbz.writestr(f"{ch_folder}/page_{page_idx:04d}.{ext}", page.data)

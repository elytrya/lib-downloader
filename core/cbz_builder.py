"""
Сборка CBZ-архива для картиночных глав (манга/манхва).
"""

import os
import re
import zipfile
from typing import List

import requests

from core.models import BookInfo, ChapterContent

IMG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://cdnlibs.org/",
}


def _sanitize_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def build_cbz(
    book: BookInfo,
    chapters: List[ChapterContent],
    output_path: str,
) -> None:
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_STORED) as cbz:
        for idx, ch in enumerate(chapters, start=1):
            if not ch.is_image_based:
                continue

            safe_ch_name = _sanitize_name(ch.info.display_name) or f"chapter-{idx}"
            ch_folder = f"{idx:04d} - {safe_ch_name}"

            for page_idx, image_url in enumerate(ch.pages, start=1):
                ext = image_url.split("?")[0].split(".")[-1]
                if len(ext) > 4 or not ext:
                    ext = "jpg"

                file_name = f"{ch_folder}/page_{page_idx:04d}.{ext}"
                try:
                    resp = requests.get(image_url, headers=IMG_HEADERS, stream=True)
                    resp.raise_for_status()

                    content = b""
                    for chunk in resp.iter_content(1024 * 64):
                        content += chunk

                    cbz.writestr(file_name, content)
                except Exception as e:
                    print(
                        f"    [!] Ошибка скачивания страницы {page_idx} (Глава {idx}): {e}"
                    )

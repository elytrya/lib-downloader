"""
це л ай (cli) программа для скачивания ранобэ/манги с сайтов ranobelib.me,
mangalib.me и упаковки выбранных глав в епаб (или в папки с картинками).

как использовать:
    python main.py <ссылка на тайтл> [-o output] [--mode epub|cbz|folders]

примеры:
    python main.py "https://ranobelib.me/ru/book/266677--slug"
    python main.py "https://mangalib.me/ru/manga/43165--ao-no-hako" --mode folders
"""

import argparse
import re
import sys
import traceback
from urllib.parse import urlparse

from cli.interactive import select_chapters
from core.asset_saver import save_chapters_as_folders
from core.auth import interactive_login, load_auth_cookies
from core.cbz_builder import build_cbz
from core.epub_builder import build_epub
from providers.registry import get_provider_for_url

GITHUB_ISSUES_URL = "https://github.com/elytrya/lib-downloader/issues"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"


def parse_args():
    parser = argparse.ArgumentParser(
        description="скачивание глав ранобэ/манги и сборка в EPUB, CBZ или папки"
    )
    parser.add_argument("url", help="ссылка на страницу тайтла")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="путь к выходному файлу или папке (по умолчанию — название тайтла)",
    )
    parser.add_argument(
        "--mode",
        choices=["epub", "cbz", "folders"],
        default=None,
        help=(
            "epub - один .epub файл; "
            "cbz - один .cbz архив (для манги); "
            "folders - папка с подпапками. "
            "если не указано - спросит в консоли."
        ),
    )
    parser.add_argument(
        "--user-agent",
        default=None,
        help="кастомный User-Agent для обхода защит (Cloudflare и т.д.)",
    )
    return parser.parse_args()


def ask_mode(is_manga: bool) -> str:
    print("\nВ каком виде сохранить главы?")
    if is_manga:
        print("  1) один .cbz файл (архив с картинками)")
    else:
        print("  1) один .epub файл (текстовая книга)")
    print("  2) папка с подпапками (картинки/текст)")
    choice = input("Выбор [1/2]: ").strip()

    if choice == "2":
        return "folders"
    return "cbz" if is_manga else "epub"


def main():
    args = parse_args()

    cookies = load_auth_cookies()
    if not cookies.get("mangalib_token") and not cookies.get("mangalib_session"):
        interactive_login()

    try:
        try:
            provider = get_provider_for_url(args.url)
        except ValueError as e:
            print(f"Ошибка: {e}", file=sys.stderr)
            sys.exit(1)

        if hasattr(provider, "session"):
            session_obj = provider.session
            headers_update = {
                "Referer": "https://mangalib.me/",
                "User-Agent": args.user_agent or DEFAULT_USER_AGENT,
            }

            if hasattr(session_obj, "headers"):
                if isinstance(session_obj.headers, dict):
                    session_obj.headers.update(headers_update)
                elif hasattr(session_obj.headers, "update"):
                    session_obj.headers.update(headers_update)
            elif hasattr(session_obj, "session") and hasattr(
                session_obj.session, "headers"
            ):
                session_obj.session.headers.update(headers_update)

        print("получаю информацию о тайтле...")
        book = provider.resolve_book(args.url)
        print(f"Тайтл: {book.title}")

        print("получаю список глав...")
        chapters = provider.list_chapters(book)
        print(f"найдено глав: {len(chapters)}")

        if not chapters:
            print("главы не найдены.")
            return

        selected = select_chapters(chapters)
        if not selected:
            print("ничего не выбрано, выход.")
            return

        print(f"скачиваю {len(selected)} глав...")
        contents = []
        for i, ch in enumerate(selected, start=1):
            print(f"  [{i}/{len(selected)}] {ch.display_name}")
            try:
                chapter_content = provider.fetch_chapter(book, ch)
                contents.append(chapter_content)
            except Exception as e:
                print(f"    не удалось скачать главу: {e}", file=sys.stderr)

        if not contents:
            print("ни одна глава не была скачана успешно.")
            return

        is_manga = any(ch.is_image_based for ch in contents)
        mode = args.mode or ask_mode(is_manga)

        safe_title = (
            "".join(c for c in book.title if c.isalnum() or c in " _-").strip()
            or book.slug
        )

        if mode == "epub":
            output_path = args.output or f"{safe_title}.epub"
            if not output_path.lower().endswith(".epub"):
                output_path += ".epub"
            print(f"собираю epub: {output_path}")
            build_epub(book, contents, output_path)

        elif mode == "cbz":
            output_path = args.output or f"{safe_title}.cbz"
            if not output_path.lower().endswith(".cbz"):
                output_path += ".cbz"
            print(f"собираю cbz: {output_path}")
            build_cbz(book, contents, output_path)

        else:
            output_dir = args.output or safe_title
            print(f"сохраняю главы в папку: {output_dir}")
            session = getattr(provider, "session", None)
            save_chapters_as_folders(book, contents, output_dir, session)

        print("готово!")

    except Exception as e:
        print("\n" + "=" * 60, file=sys.stderr)
        print("произошла непредвиденная ошибка в работе программы", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        traceback.print_exc()
        print("-" * 60, file=sys.stderr)
        print(
            f"пожалуйста, скопируйте текст ошибки выше и создайте issue на GitHub:",
            file=sys.stderr,
        )
        print(f"вот тут: {GITHUB_ISSUES_URL}", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

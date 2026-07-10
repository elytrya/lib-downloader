import argparse
import os
import sys
import traceback

from cli.interactive import select_chapters
from core.asset_saver import save_chapters_as_folders
from core.auth import interactive_login, load_auth_cookies
from core.cbz_builder import build_cbz
from core.epub_builder import build_epub
from providers.registry import get_provider_for_url

GITHUB_ISSUES_URL = "https://github.com/elytrya/lib-downloader/issues"
DOWNLOADS_DIR = "downloads"


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
        help="epub / cbz / folders. если не указано — спросит в консоли.",
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


def sanitize_title(title: str, fallback: str) -> str:
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    return safe or fallback


def default_output(safe_title: str, ext: str) -> str:
    return os.path.join(DOWNLOADS_DIR, f"{safe_title}{ext}")


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def download_chapter_pages(provider, chapter_content) -> None:
    total = len(chapter_content.pages)
    if not total:
        return
    for i, page in enumerate(chapter_content.pages, start=1):
        try:
            data, media_type = provider.download_page(page.url)
            page.data = data
            page.media_type = media_type
        except Exception as e:
            print(f"\n    [!] страница {i}/{total}: {e}", file=sys.stderr)
        sys.stdout.write(f"\r    страницы: [{i:>4}/{total}]")
        sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()


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

        if args.user_agent and getattr(provider, "session", None) is not None:
            provider.session.headers["User-Agent"] = args.user_agent

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
        total = len(selected)
        for i, ch in enumerate(selected, start=1):
            print(f"  [{i}/{total}] {ch.display_name}")
            try:
                content = provider.fetch_chapter(book, ch)
            except Exception as e:
                print(f"    не удалось скачать главу: {e}", file=sys.stderr)
                continue
            if content.is_image_based:
                download_chapter_pages(provider, content)
            contents.append(content)

        if not contents:
            print("ни одна глава не была скачана успешно.")
            return

        is_manga = any(c.is_image_based for c in contents)
        mode = args.mode or ask_mode(is_manga)
        safe_title = sanitize_title(book.title, book.slug)

        if mode == "epub":
            output_path = args.output or default_output(safe_title, ".epub")
            if not output_path.lower().endswith(".epub"):
                output_path += ".epub"
            ensure_parent(output_path)
            print(f"собираю epub: {output_path}")
            build_epub(book, contents, output_path)
        elif mode == "cbz":
            output_path = args.output or default_output(safe_title, ".cbz")
            if not output_path.lower().endswith(".cbz"):
                output_path += ".cbz"
            ensure_parent(output_path)
            print(f"собираю cbz: {output_path}")
            build_cbz(book, contents, output_path)
        else:
            output_dir = args.output or default_output(safe_title, "")
            print(f"сохраняю главы в папку: {output_dir}")
            save_chapters_as_folders(book, contents, output_dir, provider=provider)

        print("готово!")

    except Exception:
        print("\n" + "=" * 60, file=sys.stderr)
        print("произошла непредвиденная ошибка в работе программы", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        traceback.print_exc()
        print("-" * 60, file=sys.stderr)
        print(
            f"пожалуйста, скопируйте текст ошибки и создайте issue: {GITHUB_ISSUES_URL}",
            file=sys.stderr,
        )
        print("=" * 60 + "\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

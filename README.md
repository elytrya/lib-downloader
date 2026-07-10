# lib-downloader

CLI инструмент для скачивания глав манги, манхвы и ранобэ с семейств сайтов mangalib.me (mangalib.me, mangalib.org, ranobelib.me). Поддерживает сборку в один файл или сохранение структурированными папками.

## установка

```bash
pip install -r requirements.txt
```

## примеры использования

```bash
# ранобэ (текст) -> один .epub
python main.py "https://ranobelib.me/ru/book/62340--the-angel-next-door-spoils-me-rotten"

# манга/манхва (картинки) -> одна .epub с вшитыми картинками
python main.py "https://mangalib.me/ru/manga/52911--otonari-no-tenshi-sama-ni-itsu-no-ma-ni-ka-dame-ningen-ni-sareteita-ken"

# или сразу в папки chapter-N с картинками, без вопроса
python main.py "https://mangalib.me/ru/manga/52911--otonari-no-tenshi-sama-ni-itsu-no-ma-ni-ka-dame-ningen-ni-sareteita-ken" --mode folders -o "Ao no Hako"

# с указанием кастом юзер агента
python main.py "https://mangalib.me/ru/manga/52911--otonari-no-tenshi-sama-ni-itsu-no-ma-ni-ka-dame-ningen-ni-sareteita-ken" --user-agent "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1"
```

## как работает это чудо
1. определяет провайдера по домену ссылки.
2. получает список всех глав тайтла.
3. показывает список с чекбоксами:
   - `Space` — выбрать/снять одну главу;
   - `a` — выбрать/снять **все** главы сразу;
   - `Enter` — подтвердить выбор и начать скачивание.
4. для картиночных глав качает страницы с прогрессом `[i/N]` по каждой главе (как в ранобэ).
5. спрашивает (или возьмёт из `--mode`), в каком виде сохранить:
   - **epub** — один файл, подходит для ранобэ и для манги с вшитыми картинками;
   - **cbz** — картинки пакуются в zip-архив с иерархией Глава/страница.jpg;
   - **folders** — папка с подпапками `chapter-1`, `chapter-2`. картинки сохраняются в chapter-X/img/.

между запросами к апи есть небольшая задержка (`core/http_utils.py`, по умолчанию 0.5с), чтобы не ебать апи слишком часто.

## как добавить свой провайдер

1. создайте `providers/my_site.py` с классом-наследником `core.base_provider.BaseProvider`.
2. реализуйте `resolve_book`, `list_chapters`, `fetch_chapter`. если сайт не использует api.cdnlibs.org — реализация полностью своя, зависимости от `CdnlibsBaseProvider` нет.
3. переопределите `download_page(url)` если для скачивания картинок нужны свои заголовки/сессия.
4. зарегистрируйте класс в `providers/registry.py` (в списке `_PROVIDERS` или через `register_provider`).

по умолчанию все результаты кладутся в папку `downloads/` в корне проекта (можно переопределить через `-o`).

## структура проекта

```
lib-downloader/
├── main.py                    # точка входа
├── downloads/                 # сюда падают собранные .epub/.cbz и папки с главами
├── core/
│   ├── models.py              # BookInfo, ChapterInfo, ChapterContent, PageImage
│   ├── base_provider.py       # абстрактный класс провайдера
│   ├── http_utils.py          # PoliteSession и helpers для скачивания
│   ├── auth.py                # логин/сохранение токена в .env
│   ├── content_renderer.py    # JSON контент главы -> HTML
│   ├── epub_builder.py        # сборка .epub
│   ├── cbz_builder.py         # сборка .cbz
│   └── asset_saver.py         # сохранение в папки chapter-N
├── providers/
│   ├── registry.py            # реестр провайдеров
│   ├── cdnlibs_base.py        # общая часть для сайтов на api.cdnlibs.org
│   ├── mangalib.py            # mangalib.me / mangalib.org
│   └── ranobelib.py           # ranobelib.me
└── cli/
    └── interactive.py         # интерактивный чекбокс-выбор глав
```

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

## как работать это чудо:
1. определяет провайдера по домену ссылки (ranobelib.me / mangalib.me / mangalib.org).
2. получает список всех глав тайтла. (`api.cdnlibs.org/api/manga/тайтл/chapters`)
3. показывает список с чекбоксами:
   - `Space` — выбрать/снять одну главу;
   - `a` — выбрать/снять **все** главы сразу;
   - `Enter` — подтвердить выбор и начать скачивание.
4. спрашивает (или возьмёт из `--mode`), в каком виде сохранить:
   - **epub** - один файл, подходит для ранобелиба
   - **folders** - папка с подпапками `chapter-1`, `chapter-2`. картинки сохраняются в chapter-X/img/
   - **cbz**: картинки пакуются в zip архив с иерархией Глава/страница.jpg
между запросами к апи есть небольшая задержка (`core/http_utils.py`,
по умолчанию 0.5с), чтобы не ебать апи слишком часто.

## структура проекта

```
lib-downloader/
├── main.py                   # точка входа, запускает модули
├── core/
│   ├── models.py              # BookInfo, ChapterInfo, ChapterContent (текст ИЛИ картинки)
│   ├── base_provider.py       # абстрактный класс провайдера (контракт)
│   ├── content_renderer.py    # JSON-контент текстовой главы -> HTML
│   ├── epub_builder.py        # сборка итогового .epub (текст и картинки)
│   ├── asset_saver.py         # альтернативный режим: папки chapter-N
│   ├── cbz_builder.py     # Сборка .cbz
│   └── http_utils.py          # запросы с небольшой задержкой
├── providers/
│   ├── registry.py            # реестр провайдеров по доменам
│   ├── cdnlibs_base.py        # общая часть для сайтов на api.cdnlibs.org
│   ├── ranobelib.py           # ranobelib.me
│   └── mangalib.py            # mangalib.me / mangalib.org
│   └── hentailib.py            # hentailib (лень делать)
└── cli/
    └── interactive.py         # интерактивный чекбокс-выбор глав
```

## примечания

это чудо написано за вечер, так что если есть баги создавайте issues в свободное время пофикшу
todo: добавить hentailib

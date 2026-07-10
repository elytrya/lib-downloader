from typing import List

import questionary

from core.models import ChapterInfo


def select_chapters(chapters: List[ChapterInfo]) -> List[ChapterInfo]:
    if not chapters:
        return []

    choices = [
        questionary.Choice(title=ch.display_name, value=i)
        for i, ch in enumerate(chapters)
    ]

    print(
        "\nУправление: Space — выбрать/снять главу, "
        "'a' — выбрать/снять ВСЕ главы сразу, Enter — подтвердить выбор.\n"
    )

    indexes = questionary.checkbox(
        "Выберите главы для скачивания:",
        choices=choices,
    ).ask()

    if not indexes:
        return []
    return [chapters[i] for i in indexes]

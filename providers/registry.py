"""
реестр провайдеров. Чтобы добавить новый сайт нужно:
  1. cоздать providers/my_site.py с классом наследником BaseProvider.
  2. импортировать его здесь и добавить в список _PROVIDERS
     (или вызвать register_provider(...) из своего кода).
"""

from typing import List, Type

from core.base_provider import BaseProvider
from providers.mangalib import MangalibProvider
from providers.ranobelib import RanobelibProvider

_PROVIDERS: List[Type[BaseProvider]] = [
    RanobelibProvider,
    MangalibProvider,
]


def register_provider(provider_cls: Type[BaseProvider]) -> None:
    """позволяет подключать новые провайдеры извне без правки этого файла."""
    if provider_cls not in _PROVIDERS:
        _PROVIDERS.append(provider_cls)


def get_provider_for_url(url: str) -> BaseProvider:
    for provider_cls in _PROVIDERS:
        if provider_cls.supports(url):
            return provider_cls()
    supported = ", ".join(d for p in _PROVIDERS for d in p.domains)
    raise ValueError(
        f"Нет подходящего провайдера для этой ссылки. Поддерживаемые сайты: {supported}"
    )

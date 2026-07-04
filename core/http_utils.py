"""
задержка между запросами
"""

import time

import requests

DEFAULT_DELAY = 0.5


class PoliteSession:
    def __init__(self, headers: dict = None, delay: float = DEFAULT_DELAY):
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)
        self.delay = delay
        self._last_request_at = 0.0

    def get(
        self, url: str, params: dict = None, timeout: int = 30
    ) -> requests.Response:
        wait = self.delay - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        resp = self.session.get(url, params=params, timeout=timeout)
        self._last_request_at = time.monotonic()
        return resp

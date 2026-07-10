import mimetypes
import time
from typing import Optional, Tuple

import requests

DEFAULT_DELAY = 0.5
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


class PoliteSession:
    def __init__(self, headers: Optional[dict] = None, delay: float = DEFAULT_DELAY):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        if headers:
            self.session.headers.update(headers)
        self.delay = delay
        self._last_request_at = 0.0

    @property
    def headers(self):
        return self.session.headers

    @property
    def cookies(self):
        return self.session.cookies

    def get(
        self,
        url: str,
        params: Optional[dict] = None,
        timeout: int = 30,
        stream: bool = False,
        headers: Optional[dict] = None,
    ) -> requests.Response:
        wait = self.delay - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        resp = self.session.get(
            url, params=params, timeout=timeout, stream=stream, headers=headers
        )
        self._last_request_at = time.monotonic()
        return resp


def guess_media_type(url: str, response_headers: Optional[dict] = None) -> str:
    if response_headers:
        ctype = response_headers.get("Content-Type", "").split(";")[0].strip()
        if ctype.startswith("image/"):
            return ctype
    ctype, _ = mimetypes.guess_type(url.split("?")[0])
    return ctype or "image/jpeg"


def media_type_to_ext(media_type: str) -> str:
    return media_type.split("/")[-1].replace("jpeg", "jpg")


def download_bytes(
    url: str,
    headers: Optional[dict] = None,
    timeout: int = 30,
) -> Tuple[bytes, str]:
    request_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        request_headers.update(headers)
    resp = requests.get(url, headers=request_headers, timeout=timeout, stream=True)
    resp.raise_for_status()
    content = b"".join(resp.iter_content(1024 * 64))
    return content, guess_media_type(url, resp.headers)

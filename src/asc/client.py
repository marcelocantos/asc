# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

"""Thin App Store Connect REST client."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import requests

from .auth import Credentials

API_BASE = "https://api.appstoreconnect.apple.com"


class ApiError(RuntimeError):
    """Non-2xx ASC API response with status + body summary."""

    def __init__(self, status: int, body: str, url: str) -> None:
        self.status = status
        self.body = body
        self.url = url
        super().__init__(f"ASC API {status} for {url}: {body[:400]}")


class Client:
    """Bearer-auth HTTP client for ``api.appstoreconnect.apple.com``."""

    def __init__(self, creds: Credentials, session: requests.Session | None = None) -> None:
        self.creds = creds
        self.session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.creds.token()}"}

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        raw: bool = False,
    ) -> Any:
        """GET ``path`` (must start with ``/v1/``).

        Returns parsed JSON unless ``raw=True``, in which case returns
        ``(status, headers, content_bytes)``.
        """
        url = f"{API_BASE}{path}"
        if params:
            # ASC wants repeated filter keys as filter[x]= — requests handles this.
            url = f"{url}?{urlencode(params, doseq=True)}"
        resp = self.session.get(url, headers=self._headers(), timeout=60)
        if raw:
            return resp.status_code, dict(resp.headers), resp.content
        if resp.status_code >= 400:
            raise ApiError(resp.status_code, resp.text, url)
        if not resp.content:
            return None
        return resp.json()

    def get_bytes(self, path: str, params: dict[str, Any] | None = None) -> bytes:
        """GET binary payload (sales/finance reports are gzip)."""
        status, _headers, content = self.get(path, params, raw=True)
        if status == 404:
            raise FileNotFoundError(f"no report for params={params}")
        if status >= 400:
            raise ApiError(status, content.decode("utf-8", errors="replace"), path)
        return content

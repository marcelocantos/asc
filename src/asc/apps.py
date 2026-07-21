# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

"""App listing helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .client import Client


@dataclass(frozen=True)
class App:
    id: str
    name: str
    bundle_id: str
    sku: str
    primary_locale: str


def list_apps(client: Client, *, limit: int = 200) -> list[App]:
    data = client.get("/v1/apps", {"limit": limit})
    apps: list[App] = []
    for item in data.get("data") or []:
        attrs = item.get("attributes") or {}
        apps.append(
            App(
                id=item["id"],
                name=attrs.get("name") or "",
                bundle_id=attrs.get("bundleId") or "",
                sku=attrs.get("sku") or "",
                primary_locale=attrs.get("primaryLocale") or "",
            )
        )
    return apps


def find_app(
    client: Client,
    *,
    name: str | None = None,
    bundle_id: str | None = None,
    sku: str | None = None,
    app_id: str | None = None,
) -> App | None:
    for app in list_apps(client):
        if app_id and app.id == app_id:
            return app
        if bundle_id and app.bundle_id == bundle_id:
            return app
        if sku and app.sku == sku:
            return app
        if name and name.lower() in app.name.lower():
            return app
    return None

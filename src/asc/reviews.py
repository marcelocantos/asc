# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

"""Customer review listing."""

from __future__ import annotations

from dataclasses import dataclass

from .client import Client


@dataclass(frozen=True)
class Review:
    id: str
    rating: int
    title: str
    body: str
    reviewer: str
    created_date: str
    territory: str


def list_reviews(
    client: Client,
    app_id: str,
    *,
    limit: int = 50,
    sort: str = "-createdDate",
) -> list[Review]:
    data = client.get(
        f"/v1/apps/{app_id}/customerReviews",
        {
            "limit": limit,
            "sort": sort,
        },
    )
    out: list[Review] = []
    for item in data.get("data") or []:
        attrs = item.get("attributes") or {}
        out.append(
            Review(
                id=item["id"],
                rating=int(attrs.get("rating") or 0),
                title=attrs.get("title") or "",
                body=attrs.get("body") or "",
                reviewer=attrs.get("reviewerNickname") or "",
                created_date=attrs.get("createdDate") or "",
                territory=attrs.get("territory") or "",
            )
        )
    return out

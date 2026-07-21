# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

"""Sales and Trends report download + parse.

Endpoint: ``GET /v1/salesReports``
Docs: https://developer.apple.com/documentation/appstoreconnectapi/get-v1-salesreports

Daily SUMMARY SALES reports are TSV compressed with gzip (Content-Encoding /
body is gzip regardless). Rows include Product Type Identifier:

* ``1`` / ``1F`` — first-time free or paid download (units)
* ``3`` / ``3F`` — redownload
* ``7`` / ``7F`` — update

ASC Sales Trends "Units" measure corresponds to first-time downloads
(``1``/``1F``), not updates.
"""

from __future__ import annotations

import csv
import gzip
import io
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from .client import Client

Frequency = Literal["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
ReportSubType = Literal["SUMMARY", "DETAILED"]

# Product Type Identifier groups (App Store Sales reports).
FIRST_TIME = frozenset({"1", "1F", "1T", "F1"})
REDOWNLOAD = frozenset({"3", "3F", "3T", "F3"})
UPDATE = frozenset({"7", "7F", "7T", "F7"})


@dataclass(frozen=True)
class SaleRow:
    """One TSV row from a SALES SUMMARY report."""

    report_date: str
    sku: str
    title: str
    version: str
    product_type: str
    units: int
    developer_proceeds: float
    customer_price: float
    country: str
    currency: str
    parent_identifier: str
    raw: dict[str, str]

    @property
    def kind(self) -> str:
        if self.product_type in FIRST_TIME:
            return "download"
        if self.product_type in REDOWNLOAD:
            return "redownload"
        if self.product_type in UPDATE:
            return "update"
        return "other"


def _parse_tsv(text: str, report_date: str) -> list[SaleRow]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    rows: list[SaleRow] = []
    for raw in reader:
        if not raw:
            continue
        units_s = raw.get("Units") or "0"
        proceeds_s = raw.get("Developer Proceeds") or "0"
        price_s = raw.get("Customer Price") or "0"
        try:
            units = int(float(units_s))
        except ValueError:
            units = 0
        try:
            proceeds = float(proceeds_s)
        except ValueError:
            proceeds = 0.0
        try:
            price = float(price_s)
        except ValueError:
            price = 0.0
        rows.append(
            SaleRow(
                report_date=report_date,
                sku=(raw.get("SKU") or "").strip(),
                title=(raw.get("Title") or "").strip(),
                version=(raw.get("Version") or "").strip(),
                product_type=(raw.get("Product Type Identifier") or "").strip(),
                units=units,
                developer_proceeds=proceeds,
                customer_price=price,
                country=(raw.get("Country Code") or "").strip(),
                currency=(raw.get("Customer Currency") or "").strip(),
                parent_identifier=(raw.get("Parent Identifier") or "").strip(),
                raw={k: (v or "") for k, v in raw.items() if k is not None},
            )
        )
    return rows


def download_daily(
    client: Client,
    day: date,
    *,
    vendor_number: str,
    report_sub_type: ReportSubType = "SUMMARY",
) -> list[SaleRow]:
    """Download one DAILY SALES report. Empty list if Apple has no report (404)."""
    content = None
    try:
        content = client.get_bytes(
            "/v1/salesReports",
            {
                "filter[frequency]": "DAILY",
                "filter[reportSubType]": report_sub_type,
                "filter[reportType]": "SALES",
                "filter[vendorNumber]": vendor_number,
                "filter[reportDate]": day.isoformat(),
            },
        )
    except FileNotFoundError:
        return []
    text = gzip.decompress(content).decode("utf-8")
    return _parse_tsv(text, day.isoformat())


def iter_daily_range(
    client: Client,
    start: date,
    end: date,
    *,
    vendor_number: str,
) -> Iterator[SaleRow]:
    """Yield rows for each day in ``[start, end]`` inclusive (end may be today-1)."""
    if end < start:
        return
    day = start
    while day <= end:
        yield from download_daily(client, day, vendor_number=vendor_number)
        day += timedelta(days=1)


def filter_rows(
    rows: Iterable[SaleRow],
    *,
    sku: str | None = None,
    title_substr: str | None = None,
    version: str | None = None,
    kinds: frozenset[str] | None = None,
    country: str | None = None,
) -> list[SaleRow]:
    """Filter sale rows by common dimensions."""
    out: list[SaleRow] = []
    for r in rows:
        if sku is not None and r.sku != sku:
            continue
        if title_substr is not None and title_substr.lower() not in r.title.lower():
            continue
        if version is not None and r.version != version:
            continue
        if kinds is not None and r.kind not in kinds:
            continue
        if country is not None and r.country != country:
            continue
        out.append(r)
    return out


def sum_units(rows: Iterable[SaleRow]) -> int:
    return sum(r.units for r in rows)

# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

"""``asc`` command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from typing import Sequence

from . import __version__
from .apps import find_app, list_apps
from .auth import ConfigError, load_credentials
from .client import ApiError, Client
from .reviews import list_reviews
from .sales import FIRST_TIME, filter_rows, iter_daily_range, sum_units

AGENT_HELP = """\
asc — App Store Connect API CLI for studio telemetry.

Credentials (never committed):
  ~/.appstoreconnect/config.json   multi-key config (preferred)
  ~/.appstoreconnect/private_keys/AuthKey_<KEYID>.p8

config.json shape:
  {
    "issuer_id": "<uuid from ASC Keys page>",
    "vendor_number": "85112238",
    "default_key": "ops",
    "keys": {
      "ops": {
        "key_id": "UYWBJ6Y6RJ",
        "path": "~/.appstoreconnect/private_keys/AuthKey_UYWBJ6Y6RJ.p8",
        "access": ["Access to Reports", "Sales"]
      },
      "fastlane": {
        "key_id": "88JLFJQ5SK",
        "path": "~/.appstoreconnect/private_keys/AuthKey_88JLFJQ5SK.p8",
        "access": ["App Manager"]
      }
    }
  }

Role notes:
  - salesReports / financeReports need Sales, Finance, or Admin.
  - App Manager is enough for apps + customerReviews + builds.
  - Vendor number: ASC → Payments and Financial Reports (top-left).

Commands:
  asc apps                         list apps (id, name, bundle, sku)
  asc sales --app MultiMaze -d 30  daily first-time units (Trends "Units")
  asc sales --app MultiMaze --all-kinds -d 7
  asc sales --sku 201002090 --json
  asc reviews --app MultiMaze      recent customer reviews
  asc whoami                       print resolved key + vendor

Filters for sales:
  --kind download|update|redownload|other   (repeatable; default: download)
  --version 3.1.0
  --country US
  --days N  /  --since YYYY-MM-DD --until YYYY-MM-DD

Output:
  Human tables on stdout by default; --json for machine-readable.
  Errors on stderr. Exit 0 ok, 1 API/config error, 2 usage.

Agent tips:
  - Prefer --json when chaining into jq or another tool.
  - Default sales kind is first-time download (Product Type 1/1F), which
    matches ASC Sales Trends "Units". Pass --all-kinds for updates too.
  - Daily reports lag ~1 day; today is usually 404.
  - Use --key ops (or whatever Sales-capable key is named) when the
    default lacks Sales access.
"""


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def _date_range(args: argparse.Namespace) -> tuple[date, date]:
    today = date.today()
    if args.since or args.until:
        start = _parse_date(args.since) if args.since else today - timedelta(days=30)
        end = _parse_date(args.until) if args.until else today - timedelta(days=1)
    else:
        days = args.days if args.days is not None else 30
        end = today - timedelta(days=1)
        start = end - timedelta(days=days - 1)
    return start, end


def _client(args: argparse.Namespace) -> Client:
    creds = load_credentials(key=args.key)
    return Client(creds)


def cmd_whoami(args: argparse.Namespace) -> int:
    creds = load_credentials(key=args.key)
    payload = {
        "key_name": creds.key_name,
        "key_id": creds.key_id,
        "issuer_id": creds.issuer_id,
        "vendor_number": creds.vendor_number,
        "access": list(creds.access),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"key       {creds.key_name or '-'} ({creds.key_id})")
        print(f"issuer    {creds.issuer_id}")
        print(f"vendor    {creds.vendor_number or '(unset)'}")
        print(f"access    {', '.join(creds.access) or '(unknown)'}")
    return 0


def cmd_apps(args: argparse.Namespace) -> int:
    client = _client(args)
    apps = list_apps(client)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": a.id,
                        "name": a.name,
                        "bundle_id": a.bundle_id,
                        "sku": a.sku,
                        "primary_locale": a.primary_locale,
                    }
                    for a in apps
                ],
                indent=2,
            )
        )
        return 0
    if not apps:
        print("no apps", file=sys.stderr)
        return 0
    w_name = max(len(a.name) for a in apps)
    w_bundle = max(len(a.bundle_id) for a in apps)
    for a in apps:
        print(f"{a.id}  {a.name:<{w_name}}  {a.bundle_id:<{w_bundle}}  sku={a.sku}")
    return 0


def _resolve_sku(client: Client, args: argparse.Namespace) -> str | None:
    if args.sku:
        return args.sku
    if not args.app:
        return None
    app = find_app(client, name=args.app, bundle_id=args.app, app_id=args.app)
    if not app:
        raise SystemExit(f"asc: app not found: {args.app}")
    return app.sku or None


def cmd_sales(args: argparse.Namespace) -> int:
    client = _client(args)
    vendor = args.vendor or client.creds.vendor_number
    if not vendor:
        print(
            "asc: vendor_number required (config.json or --vendor)",
            file=sys.stderr,
        )
        return 1

    start, end = _date_range(args)
    sku = _resolve_sku(client, args)
    title = args.title

    rows = list(iter_daily_range(client, start, end, vendor_number=vendor))

    kinds: frozenset[str] | None
    if args.all_kinds:
        kinds = None
    elif args.kind:
        kinds = frozenset(args.kind)
    else:
        kinds = frozenset({"download"})

    filtered = filter_rows(
        rows,
        sku=sku,
        title_substr=title,
        version=args.version,
        kinds=kinds,
        country=args.country,
    )

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "date": r.report_date,
                        "sku": r.sku,
                        "title": r.title,
                        "version": r.version,
                        "product_type": r.product_type,
                        "kind": r.kind,
                        "units": r.units,
                        "country": r.country,
                        "proceeds": r.developer_proceeds,
                        "price": r.customer_price,
                        "currency": r.currency,
                    }
                    for r in filtered
                ],
                indent=2,
            )
        )
        return 0

    if args.by == "day":
        by_day: dict[str, int] = defaultdict(int)
        for r in filtered:
            by_day[r.report_date] += r.units
        for day in sorted(by_day):
            print(f"{day}  {by_day[day]}")
        print(f"total  {sum(by_day.values())}  ({start}..{end})")
    elif args.by == "country":
        by_c: dict[str, int] = defaultdict(int)
        for r in filtered:
            by_c[r.country] += r.units
        for c, u in sorted(by_c.items(), key=lambda x: (-x[1], x[0])):
            print(f"{c:4}  {u}")
        print(f"total  {sum(by_c.values())}")
    elif args.by == "version":
        by_v: dict[str, int] = defaultdict(int)
        for r in filtered:
            by_v[r.version or "?"] += r.units
        for v, u in sorted(by_v.items(), key=lambda x: (-x[1], x[0])):
            print(f"{v:10}  {u}")
        print(f"total  {sum(by_v.values())}")
    else:  # row
        for r in filtered:
            print(
                f"{r.report_date}  {r.units:4d}  {r.kind:10}  {r.product_type:3}  "
                f"{r.country:2}  v{r.version or '?':8}  {r.title}  ({r.sku})"
            )
        print(f"total  {sum_units(filtered)}  rows={len(filtered)}")
    return 0


def cmd_reviews(args: argparse.Namespace) -> int:
    client = _client(args)
    app = find_app(
        client,
        name=args.app,
        bundle_id=args.app,
        app_id=args.app,
        sku=args.sku,
    )
    if not app:
        print(f"asc: app not found: {args.app or args.sku}", file=sys.stderr)
        return 1
    reviews = list_reviews(client, app.id, limit=args.limit)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": r.id,
                        "rating": r.rating,
                        "title": r.title,
                        "body": r.body,
                        "reviewer": r.reviewer,
                        "created_date": r.created_date,
                        "territory": r.territory,
                    }
                    for r in reviews
                ],
                indent=2,
            )
        )
        return 0
    for r in reviews:
        stars = "*" * r.rating
        print(f"{r.created_date[:10]}  {stars:5}  {r.territory:2}  {r.reviewer}")
        if r.title:
            print(f"  {r.title}")
        body = r.body.replace("\n", " ").strip()
        if body:
            print(f"  {body[:200]}")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="asc",
        description="App Store Connect API CLI — sales, reviews, telemetry.",
    )
    p.add_argument("--version", action="version", version=f"asc {__version__}")
    p.add_argument(
        "--help-agent",
        action="store_true",
        help="print agent-oriented help and exit",
    )
    p.add_argument(
        "--key",
        default=None,
        help="named key from config.json (default: config default_key)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON on stdout",
    )

    sub = p.add_subparsers(dest="cmd", required=False)

    who = sub.add_parser("whoami", help="show resolved credentials")
    who.set_defaults(func=cmd_whoami)

    apps_p = sub.add_parser("apps", help="list apps")
    apps_p.set_defaults(func=cmd_apps)

    sales_p = sub.add_parser("sales", help="download sales report units")
    sales_p.add_argument("--app", help="app name / bundle id / ASC app id")
    sales_p.add_argument("--sku", help="app SKU (from ASC or `asc apps`)")
    sales_p.add_argument("--title", help="substring match on report Title")
    sales_p.add_argument("--version", help="filter Version column")
    sales_p.add_argument("--country", help="filter Country Code (e.g. US)")
    sales_p.add_argument(
        "--kind",
        action="append",
        choices=["download", "update", "redownload", "other"],
        help="product kind (repeatable; default: download)",
    )
    sales_p.add_argument(
        "--all-kinds",
        action="store_true",
        help="include downloads, updates, redownloads",
    )
    sales_p.add_argument("-d", "--days", type=int, default=None, help="lookback days")
    sales_p.add_argument("--since", help="start date YYYY-MM-DD")
    sales_p.add_argument("--until", help="end date YYYY-MM-DD")
    sales_p.add_argument("--vendor", help="override vendor number")
    sales_p.add_argument(
        "--by",
        choices=["day", "country", "version", "row"],
        default="day",
        help="aggregate (default: day)",
    )
    sales_p.set_defaults(func=cmd_sales)

    rev = sub.add_parser("reviews", help="list customer reviews")
    rev.add_argument("--app", help="app name / bundle id / ASC app id")
    rev.add_argument("--sku", help="app SKU")
    rev.add_argument("--limit", type=int, default=20)
    rev.set_defaults(func=cmd_reviews)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    # Allow `asc --help-agent` without a subcommand.
    if "--help-agent" in argv and not any(
        a in argv for a in ("apps", "sales", "reviews", "whoami")
    ):
        print(AGENT_HELP, end="")
        return 0
    args = parser.parse_args(argv)
    if getattr(args, "help_agent", False):
        print(AGENT_HELP, end="")
        return 0
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return int(args.func(args))
    except ConfigError as e:
        print(f"asc: {e}", file=sys.stderr)
        return 1
    except ApiError as e:
        print(f"asc: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

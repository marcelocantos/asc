# asc

App Store Connect API CLI for studio telemetry — sales units, customer
reviews, and app inventory. No browser scraping.

## Install

```sh
cd ~/work/github.com/marcelocantos/asc
uv pip install -e .
```

Requires Python 3.10+ and credentials under `~/.appstoreconnect/`.

## Credentials

```sh
mkdir -p ~/.appstoreconnect/private_keys
# Save AuthKey_<KEYID>.p8 once from ASC → Users and Access → Integrations → Keys
chmod 600 ~/.appstoreconnect/private_keys/AuthKey_*.p8
```

`~/.appstoreconnect/config.json` (mode `600`):

```json
{
  "issuer_id": "<uuid from Keys page>",
  "vendor_number": "<from Payments and Financial Reports>",
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
```

**Sales reports need a key with Sales, Finance, or Admin access.** App
Manager is enough for apps and reviews, not `salesReports`.

Vendor number: App Store Connect → **Payments and Financial Reports**
(top-left under the legal entity name).

## Usage

```sh
asc whoami
asc apps
asc sales --app MultiMaze -d 30          # first-time units (Trends "Units")
asc sales --app MultiMaze --all-kinds -d 7
asc sales --sku 201002090 --by country --version 3.1.0
asc --json sales --app MultiMaze
asc reviews --app MultiMaze --limit 10
asc --help-agent
```

`--json` and `--key` are parent-parser flags. They must precede the
subcommand (`asc --json apps`, `asc --key ops whoami`). Suffix form
(`asc apps --json`, `asc whoami --key ops`) exits 2.

Default sales kind is **download** (Product Type `1` / `1F`) — the same
measure ASC Sales Trends labels "Units". Pass `--all-kinds` to include
updates (`7`/`7F`) and redownloads (`3`/`3F`).

Daily reports lag about one day; "today" is usually missing (404).

## Library

```python
from asc.auth import load_credentials
from asc.client import Client
from asc.sales import iter_daily_range, filter_rows, sum_units
from datetime import date, timedelta

client = Client(load_credentials())
end = date.today() - timedelta(days=1)
start = end - timedelta(days=29)
rows = list(iter_daily_range(client, start, end, vendor_number=client.creds.vendor_number))
mm = filter_rows(rows, sku="201002090", kinds=frozenset({"download"}))
print(sum_units(mm))
```

## License

Apache-2.0.

# AGENTS.md

## Project

`asc` — App Store Connect API CLI for studio telemetry (sales units,
reviews, app inventory). Python 3.10+, installed via `uv pip install -e .`.

## Credentials

Never commit keys. Config lives only under `~/.appstoreconnect/`:

- `config.json` — issuer, vendor number, named keys
- `private_keys/AuthKey_<KEYID>.p8`

Sales needs a key with **Sales / Finance / Admin**. The Squz studio
`ops` key (`UYWBJ6Y6RJ`) has Access to Reports + Sales. The `fastlane`
key is App Manager only (ship/match).

Vendor number for Squz: `85112238`.

## Commands

```
asc whoami
asc apps
asc sales --app MultiMaze -d 30
asc reviews --app MultiMaze
asc --help-agent
```

## Delivery

Delivery: merged to master. First useful slice is `sales` + `apps` +
`reviews` against a live Sales-capable key.

## Gates

profile: tool

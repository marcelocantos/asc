# Entropy audit — `asc`

Date: 2026-08-22
Mode: full (entropy + explicit hygiene validation)
Auditor snapshot is this working tree, not `origin/master`.

## Executive summary

- **Snapshot:** `/Users/marcelo/work/github.com/marcelocantos/asc`
  - Branch: `master`
  - HEAD: `03dfc5829566df946a7eb49f02ec06dbf604f30f` (`03dfc58 Retire 🎯T1: MultiMaze sales units proven via ASC API`)
  - Tracking: `master...origin/master [ahead 1, behind 1]`
    - Local-only: `03dfc58` (🎯T1 `status: achieved`)
    - Remote-only: `3c4d9e2` (same message; 🎯T1 still `status: identified`)
  - Initial dirty state (`git status --porcelain=v1 -b` before any write):
    ```
    ## master...origin/master [ahead 1, behind 1]
    ?? .claudia-mcp-home/
    ```
    `.claudia-mcp-home/` is user-owned untracked data. It was not modified, staged, or deleted.
- **Scope:** tracked Python CLI (`src/asc/`, `tests/`, `pyproject.toml`, `Makefile`, `README.md`, `AGENTS.md`, `bullseye.yaml`). Language companions applied: `python.md`, `bash.md` (Makefile glue only), `journeys.md` (owner-visible CLI path).
- **Headline mechanism:** A small acyclic CLI with a clean module DAG, but parent-parser-only `--json`/`--key` make the documented machine-readable commands fail, and the only standing oracle is TSV parse/filter — so that CLI contract never had a chance to fail a test.
- **Highest-consequence findings:** ENT-001 (documented `--json` after subcommand exits 2), ENT-002 (no CLI/auth/HTTP tests and no CI).
- **Unverified residue:** Dependabot/OSV vulnerability content (alerts disabled; no scanner installed); whether `api_key.json` still has a live ship/match consumer; weekly/monthly sales reports; pagination beyond one page of apps/reviews.

## Scope and exclusions

Included: `src/asc/*.py`, `tests/test_sales_parse.py`, packaging/docs/gates listed above, plus a live shipped-path smoke against `~/.appstoreconnect/` (results redacted to exit codes and counts).

Named exclusions (not silent omissions):

| Path | Role |
|---|---|
| `src/asc.egg-info/` | setuptools generate; gitignored |
| `src/asc/__pycache__/`, `tests/__pycache__/`, `.pytest_cache/`, `.ruff_cache/` | bytecode/cache |
| `.claudia-mcp-home/` | untracked, user-owned; not in `.gitignore` |
| `~/.appstoreconnect/` | credentials, not in repo; used only for live smoke |

No `.github/workflows/`, no `hygiene.yaml`, no lockfile, no `CLAUDE.md`.

## Commands run

| Command | Version / notes | Exit | Shipped vs auxiliary | Relevant output / limitations |
|---|---|---|---|---|
| `git status --porcelain=v1 -b`; `git rev-parse HEAD`; `git log -1` | git | 0 | auxiliary | Snapshot above. |
| `git log --oneline origin/master..HEAD` / reverse | existing `origin/master` ref; no fetch | 0 | auxiliary | Ahead `03dfc58`, behind `3c4d9e2`; diff is `bullseye.yaml` T1 status only. |
| `python3 --version` | Python 3.13.0 (`~/.py`) | 0 | auxiliary | Declared requires-python `>=3.10`. |
| `uv --version` | uv 0.6.14 | 0 | auxiliary | Matches project install path. |
| `python3 -c 'import jwt,requests,asc; …'` | PyJWT 2.13.0, requests 2.33.1, asc 0.1.0 from `src/` | 0 | shipped import | Confirms editable install. |
| `make test` → `pytest` | pytest 9.0.3 | 0 | shipped hermetic | `tests/test_sales_parse.py .` — 1 passed in 0.05s. pytest-asyncio deprecation warning from global venv, not this repo. |
| `python3 -m py_compile src/asc/*.py` | 3.13.0 | 0 | auxiliary syntax | Not a test. |
| `make bullseye` | Makefile | 2 | auxiliary local gate | `✓ syntax` then `✗ dirty tree` because of user-owned `?? .claudia-mcp-home/`. Does not run pytest. |
| `ruff check src tests` | ruff 0.15.20 | 1 | auxiliary | `F401` unused `FIRST_TIME` import at `src/asc/cli.py:20`. No ruff config in repo. |
| `asc --version` | shipped CLI 0.1.0 | 0 | shipped | `asc 0.1.0` |
| `asc --help` | shipped | 0 | shipped | 19 lines. |
| `asc --help-agent` | shipped | 0 | shipped | 55 lines. |
| `asc` (no subcommand) | shipped | 2 | shipped | Usage, as documented. |
| `asc whoami` | shipped, live creds | 0 | shipped | Output not copied (contains issuer/key). Proves config load only — no Apple HTTP. |
| `asc apps --json` | shipped | 2 | shipped (documented form) | `unrecognized arguments: --json` |
| `asc --json apps` | shipped (prefix form) | 0 | shipped | 19 apps; MultiMaze/sku presence not printed here. |
| `asc sales --app MultiMaze --json -d 1` | shipped (documented form) | 2 | shipped | `unrecognized arguments: --json` |
| `asc --json sales --app MultiMaze -d 1` | shipped prefix | 0 | shipped | JSON path works when `--json` precedes the subcommand. |
| `asc sales --app MultiMaze -d 7` | shipped human table | 0 | shipped | `total` line present; unit counts omitted. |
| `asc reviews --app MultiMaze --json` | shipped documented form | 2 | shipped | same `--json` rejection. |
| `asc whoami --json` / `asc whoami --key ops` | shipped | 2 | shipped | `--json` and `--key` after subcommand both rejected. |
| `python3` argparse matrix on `build_parser().parse_args` | auxiliary | 0 | auxiliary | See ENT-001; documents README examples as FAIL. |
| `gh repo view` / `gh api …/actions/workflows` / branch protection / vulnerability-alerts | gh | 0/404 | auxiliary | Public repo; no workflow files; branch not protected; vulnerability alerts disabled; secret scanning + push protection enabled. Workflow list contains only GitHub's dynamic `Dependency Graph`. |
| `/Users/marcelo/.claude/skills/hygiene/hygiene_check.py` | hygiene skill | 1 | auxiliary | `FileNotFoundError: …/asc/hygiene.yaml`. Full output in Hygiene posture. |
| `python3 -c 'import pytest_cov'` | n/a | 1 | auxiliary | pytest-cov not installed; coverage not collected. Did not install. |
| `command -v pip-audit osv-scanner pipdeptree mypy jscpd` | n/a | 1 | auxiliary | Not installed. Did not install. |

Limitations: ruff/mypy/jscpd/pip-audit are not declared by the repo. Live Apple calls depend on this machine's `~/.appstoreconnect/` and network; they are evidence, not a standing CI oracle.

## Dimension vector

First audit; change-from-baseline is n/a.

| Dimension | State | Evidence summary | Change from baseline |
|---|---|---|---|
| Architecture topology | healthy | Acyclic DAG: `cli` → `{apps,reviews,sales,auth,client}`; `apps`/`reviews`/`sales` → `client` → `auth`. One deployable (`project.scripts.asc`). | n/a (first audit) |
| Redundancy / sources of truth | concern | Studio vendor/key/SKU copied in README, AGENTS, `cli.AGENT_HELP`, `auth` docstring, `bullseye.yaml`. Three credential document shapes in `auth.py`. | n/a |
| Change amplification | concern | `--json`/`--key` live only on the parent parser; help text + README must move together with argparse. Adding a command already means `cli.py` plus a module — acceptable at this size except for the duplicated identity block. | n/a |
| Local code quality | healthy | Linear modules, frozen dataclasses, one ruff F401, no cycles. `find_app` substring match is the only local hazard. | n/a |
| Correctness / verification | critical | Documented `--json` invocations fail now (ENT-001). Standing tests: 1 parse/filter case. No CLI/auth/client tests. No CI. Live human `sales` still works. | n/a |
| Security / dependencies | concern | Secrets stay off-repo (`.p8`/`config.json` untracked; GitHub secret scanning + push protection on). No lockfile, unpinned `PyJWT`/`requests`, vulnerability alerts disabled, inline PEM accepted in two loaders. | n/a |
| Build / release / operations | concern | `make test` is local pytest only. `make bullseye` is `py_compile` + clean-tree, not tests. No Actions workflows, no branch protection, no lockfile, no release wiring. | n/a |
| Documentation / governance | concern | README/AGENTS/`--help-agent` are otherwise aligned with the DAG, but they teach the broken `--json` suffix. `hygiene.yaml` absent. 🎯T1 achieved locally only. | n/a |

Not collapsed to a scalar.

## Observed architecture

```
python -m asc / console_script "asc"
        │
        ▼
     cli.main ── argparse (parent: --json --key --help-agent --version)
        │
        ├─ cmd_whoami ── load_credentials (no HTTP)
        ├─ cmd_apps    ── list_apps ── Client.get /v1/apps
        ├─ cmd_sales   ── find_app + iter_daily_range ── Client.get_bytes /v1/salesReports
        └─ cmd_reviews ── find_app + list_reviews ── Client.get /v1/apps/{id}/customerReviews
                              │
                              ▼
                           Client ── requests ── https://api.appstoreconnect.apple.com
                              │
                              ▼
                    auth.Credentials.token (ES256 JWT, 19 min TTL)
```

**Declared and observed that agree**

- Studio telemetry CLI over App Store Connect REST, not browser scraping (`AGENTS.md`, `README.md`, 🎯T1 context).
- Credentials only under `~/.appstoreconnect/`; nothing secret in git (grep found no PEM; `config.json`/`*.p8` are outside the repo).
- Default sales measure is first-time download (`1`/`1F`) to match Trends "Units" (`sales.py:36-66`, `cli.py:178-184`).
- Delivery is merge to `master`; package is a console script (`pyproject.toml:40-41`).

**Observed, inferred from code**

- Three credential documents: `config.json` keys map (`path`), flat `config.json` (`key_path` + optional embedded `key`), legacy `api_key.json` (`auth.py:102-179`).
- `Client` is the only HTTP boundary; JSON:API pagination `links.next` is ignored (`apps.py:22-36`, `reviews.py:24-52`).
- `find_app` treats `--app` as id, bundle id, *or* case-insensitive name substring (`apps.py:47-55`, `cli.py:151-157`).

**Contradictions**

- README L59 and `AGENT_HELP` L57 show `--json` after the subcommand; argparse defines `--json`/`--key` only on the parent parser (`cli.py:305-316`). Documented invocations exit 2 (ENT-001).
- 🎯T1 acceptance still claims unit tests + live `asc sales`/`apps`/`reviews`; hermetic coverage is parse-only. `apps`/`reviews --json` as commonly written do not run.

**Unknown intent (owner judgment)**

- Keep legacy `api_key.json` / embedded PEM for ship/match, or delete now that `config.json` keys maps exist?
- Should `--help-agent` examples stay Squz-specific (real key ids, vendor `85112238`, sku `201002090`) in a public repo, or become placeholders?

## Findings

### ENT-001: Parent-only `--json`/`--key` reject the documented CLI forms

- **Priority:** P1
- **Dimensions:** Correctness / verification; Documentation / governance; Change amplification
- **Status:** observed fact
- **Evidence:**
  - `--json` and `--key` are added on the parent parser only, then `add_subparsers` (`src/asc/cli.py:305-316`).
  - Shipped help documents `asc sales --sku 201002090 --json` (`src/asc/cli.py:57`).
  - README documents `asc sales --app MultiMaze --json` (`README.md:59`).
  - Live: `asc apps --json`, `asc sales --app MultiMaze --json -d 1`, `asc reviews --app MultiMaze --json`, `asc whoami --json`, `asc whoami --key ops` all exit 2 with `unrecognized arguments: --json` (or `--key ops`).
  - Prefix form works: `asc --json apps` exit 0 (19 apps); `asc --json sales --app MultiMaze -d 1` exit 0; `asc --json whoami` exit 0.
  - Auxiliary `build_parser().parse_args(["sales", "--app", "MultiMaze", "--json"])` → SystemExit 2; `["--json", "sales", "--app", "MultiMaze"]` parses.
- **Mechanism:** argparse does not attach parent optional flags to subcommands unless they are registered on each subparser (`parents=`). Anyone following README, `--help-agent`, or typical `tool subcmd --flag` order never reaches `cmd_sales`/`cmd_apps`. Agents are explicitly told to prefer `--json` (`cli.py:72`).
- **Blast radius:** every machine-readable invocation and any `--key` override written after the subcommand. Human `asc sales --app MultiMaze -d N` still works (confirmed live, exit 0). Wrong-path users see a usage error, not silently wrong totals.
- **Counterevidence checked:** T1 live smoke used `asc sales --app MultiMaze -d 30` without `--json` (`bullseye.yaml:22`). `asc --help` lists `--json` on the parent usage line, which is technically accurate and easy to miss. No test calls `build_parser`.
- **Smallest coherent remediation:** give every subparser the parent `--json`/`--key` (shared `parents=[common]` parser). Keep the parent copies so `asc --json sales …` still works. Update one golden example list after the parser accepts both orders.
- **Verification:** hermetic `parse_args` cases for README lines 53–61, including `["sales", "--app", "MultiMaze", "--json"]` and `["whoami", "--key", "ops"]`. A regression is a SystemExit 2 on those vectors.
- **Ratchet candidate:** pytest module `tests/test_cli_parse.py` run by `make test` and, once CI exists, the pytest job.

### ENT-002: Standing oracle covers TSV parse only; owner-visible CLI/auth/HTTP are ungated

- **Priority:** P1
- **Dimensions:** Correctness / verification; Build / release / operations
- **Status:** observed fact
- **Evidence:**
  - Only test file: `tests/test_sales_parse.py` (24 lines) — `_parse_tsv` + `filter_rows`/`sum_units` for kinds `download`/`update`.
  - `make test` is `pytest` (`Makefile:1-2`). `make bullseye` is `py_compile` + clean tree (`Makefile:4-7`), not pytest.
  - No `.github/workflows/` locally or on GitHub (`gh api …/contents/.github/workflows` → 404).
  - ENT-001 survived 🎯T1 retirement because no test instantiates `build_parser`.
  - Live human `asc sales --app MultiMaze -d 7` exit 0 this audit; `asc whoami` exit 0 (local JWT material only). That is a one-machine smoke, not a wired journey.
- **Mechanism:** the product is the CLI + JWT + gzip sales report path. The hermetic net cannot fail if argparse, `load_credentials`, `Client.get`, or `gzip.decompress` break. 🎯T1's live bullets were an attestation in a commit message, not an oracle loop.
- **Blast radius:** every future change to `cli.py`, `auth.py`, `client.py`, `apps.py`, `reviews.py`. Parse tests would still pass.
- **Counterevidence checked:** 🎯T1 acceptance honestly says "Unit tests cover TSV parse + download/update kind filtering" (`bullseye.yaml:25`) — that claim holds. `Client.__init__` accepts an injected `requests.Session` (`client.py:31-33`), so HTTP *could* be faked without Apple. Journeys doctrine requires a standing owner-visible slice or an explicit exception; neither is in-repo.
- **Smallest coherent remediation:** (1) hermetic argparse + credential-loader tests with tmp `config.json` and a disposable PEM; (2) `Client` tests with a fake session for 200/404/4xx; (3) one live journey (`asc --json sales --app MultiMaze -d 1`) gated on credentials, failing loud as OUTAGE when `~/.appstoreconnect` is missing rather than skip-and-green. Wire (1)–(2) to `make test` / CI.
- **Verification:** a test that would have failed before ENT-001's parser fix; CI job whose absence is itself a fail once declared.
- **Ratchet candidate:** `make test` plus a GitHub Actions `pytest` job on `push`/`pull_request`; optional `command:` live smoke with `manual`/`skipped` hygiene once `hygiene.yaml` exists.

### ENT-003: Studio identity and credential examples are copied in five places

- **Priority:** P2
- **Dimensions:** Redundancy / sources of truth; Change amplification; Documentation / governance
- **Status:** observed fact
- **Evidence:** vendor `85112238`, key ids `UYWBJ6Y6RJ` / `88JLFJQ5SK`, sku `201002090` appear in `README.md:32-38,58`, `AGENTS.md:16-19`, `src/asc/cli.py:32-57` (`AGENT_HELP`), `src/asc/auth.py:12-22`, `bullseye.yaml:22-31`. The JSON config blob is duplicated between README, `AGENT_HELP`, and the `auth` module docstring.
- **Mechanism:** key rotation, vendor change, or a second studio requires a five-file edit or `--help-agent` lies. This is a public repository (`gh`: `visibility: public`), so the copies are also a long-lived studio fingerprint (key *ids*, not PEMs).
- **Blast radius:** docs + shipped help + agent instructions. Runtime still reads `~/.appstoreconnect/config.json`; wrong examples do not mint tokens.
- **Counterevidence checked:** no issuer UUID is committed (placeholders only). GitHub secret scanning and push protection are enabled. PEMs are mode `600` on this host. Key ids are JWT `kid` values, not private keys — this is duplication and fingerprinting, not a committed secret.
- **Smallest coherent remediation:** keep Squz facts in `AGENTS.md` (operator runbook) and `bullseye.yaml` (acceptance). Make `AGENT_HELP` / README examples use placeholders (`<KEYID>`, `<VENDOR>`). One function or file can own the help text used by `--help-agent`.
- **Verification:** a test or grep ratchet that `AGENT_HELP` does not contain the production key ids, *or* a single-source include if the owner wants them kept.
- **Ratchet candidate:** hygiene `file:` / test asserting help text uses placeholders; alternatively an explicit accepted-risk note in `hygiene.yaml`.

### ENT-004: Three credential document shapes with mismatched field names and no tests

- **Priority:** P2
- **Dimensions:** Redundancy / sources of truth; Correctness / verification; Security / dependencies
- **Status:** observed fact
- **Evidence:**
  - Keys-map loader uses `entry["path"]` (`auth.py:120-143`).
  - Flat `config.json` uses `key_path` and may embed `raw["key"]` PEM (`auth.py:145-160`).
  - Legacy `api_key.json` uses `key` or `key_path` (`auth.py:163-179`).
  - Prefer `config.json` over legacy (`auth.py:102-105`).
  - Zero tests under `tests/` import `asc.auth`.
- **Mechanism:** a working keys-map config with `"path"` copied into a flat file silently ignores `path` and looks for `AuthKey_<id>.p8` or `key_path`. Embedded PEM is a second secret location besides `private_keys/`. A loader bug cannot fail CI (ENT-002).
- **Blast radius:** anyone editing `~/.appstoreconnect/config.json`; ship/match tools still on `api_key.json`. Wrong shape → `ConfigError` or unexpected file path, not a call with a mixed-up key *unless* an embedded `key` is stale relative to the `.p8`.
- **Counterevidence checked:** docstring advertises the legacy shape as intentional (`auth.py:28-29`). Live `asc whoami` exit 0 shows the keys-map path works on this host. README documents only the keys-map shape, which is the preferred one.
- **Smallest coherent remediation:** keep one preferred format (keys map); add hermetic tests for it; if legacy must stay, test `path` vs `key_path` so a misplaced field errors loudly. Stop accepting inline PEM unless a named compatibility test says so.
- **Verification:** tmp-directory tests for keys-map success, unknown `--key`, missing `issuer_id`, and a flat document with `path` (not `key_path`) asserting `ConfigError`.
- **Ratchet candidate:** those tests in `make test`.

### ENT-005: No lockfile, no CI, vulnerability alerts off, unpinned runtime deps

- **Priority:** P2
- **Dimensions:** Security / dependencies; Build / release / operations
- **Status:** observed fact
- **Evidence:**
  - `pyproject.toml:27-30` — `PyJWT[crypto]>=2.8`, `requests>=2.31`; no `uv.lock` / `requirements.txt`.
  - No workflow files; Actions API lists only dynamic `Dependency Graph`.
  - `gh api repos/marcelocantos/asc/vulnerability-alerts` → 404 "Vulnerability alerts are disabled."
  - `dependabot_security_updates: disabled`. Secret scanning + push protection enabled (healthy exception).
  - `make bullseye` does not run pytest (`Makefile:4-7`).
- **Mechanism:** the next `uv pip install -e .` can pull a new PyJWT/requests; nothing in CI notices; Dependabot will not open PRs. Reproducible installs and known-vuln gating are absent.
- **Blast radius:** every install of this public package; JWT minting and TLS HTTP are the trust boundary to Apple.
- **Counterevidence checked:** this machine currently has PyJWT 2.13.0 and requests 2.33.1, and live sales HTTP succeeded. pip-audit/osv-scanner are not installed; this finding is the missing *gate*, not a named CVE. Did not install scanners.
- **Smallest coherent remediation:** add a pytest Actions workflow; enable Dependabot or GitHub vulnerability alerts; optionally pin via `uv lock` if the owner wants install reproducibility. Do not add TOML beyond existing `pyproject.toml`.
- **Verification:** a workflow file that exists and a Dependabot/alerts setting that `gh api` reports enabled; `make test` in that job.
- **Ratchet candidate:** hygiene items `ci_job`, `scanner`/`gh_setting` once `hygiene.yaml` is declared.

### ENT-006: `find_app` last-match rule is a case-insensitive substring

- **Priority:** P3
- **Dimensions:** Local code quality; Correctness / verification
- **Status:** inference
- **Evidence:** `apps.py:54-55` — `if name and name.lower() in app.name.lower()`. Callers pass the same `--app` string as `name`, `bundle_id`, and `app_id` (`cli.py:151-157`, `cli.py:252-257`). Exact id/bundle/sku win first. `list_apps` is unpaginated `limit=200` (`apps.py:22-23`). Live `--json` prefix listing returned 19 apps.
- **Mechanism:** `--app Maze` (or a prefix of another title) binds the first substring hit in Apple's list order. With 19 apps this is no longer hypothetical, though it only bites when names nest.
- **Blast radius:** `sales` SKU resolution and `reviews` app id. Wrong app → wrong units/reviews, exit 0.
- **Counterevidence checked:** exact `app_id` / `bundle_id` / `sku` comparisons run first. T1 uses `MultiMaze`, which is the intended title. No second app name was printed in this audit.
- **Smallest coherent remediation:** require exact name match (case-insensitive) unless `--app` is unambiguously an id/bundle/sku; on multiple hits, exit 1 with the candidates.
- **Verification:** unit test over a fake `list_apps` list with `MultiMaze` and `MultiMaze Pro`.
- **Ratchet candidate:** that unit test.

### ENT-007: `make bullseye` is not a test gate

- **Priority:** P3
- **Dimensions:** Build / release / operations; Correctness / verification
- **Status:** observed fact
- **Evidence:** `Makefile:4-7` runs `python3 -m py_compile src/asc/*.py` and `git status --porcelain`. This audit: syntax OK, then fail on `?? .claudia-mcp-home/` (user-owned). pytest is a different target.
- **Mechanism:** a green `make bullseye` can coincide with a red `make test`, and a dirty unrelated directory fails the gate even when tests pass. Two local "done" signals that do not measure the same property.
- **Blast radius:** whoever uses `make bullseye` as the merge/target check.
- **Counterevidence checked:** `AGENTS.md` Gates profile is `tool`; it does not claim `make bullseye` runs pytest. The dirty-tree check is useful as an isolation rule, just not as a correctness oracle.
- **Smallest coherent remediation:** make `bullseye` depend on `test`, or delete the target if unused. Add `.claudia-mcp-home/` to `.gitignore` only if the owner wants that dir to exist in this clone.
- **Verification:** `make bullseye` fails when `tests/test_sales_parse.py` is broken.
- **Ratchet candidate:** `Makefile` `bullseye: test` plus hygiene `make_target: test`.

## Redundancy and competing-source-of-truth inventory

| Fact | Owners | Drift risk |
|---|---|---|
| Package version `0.1.0` | `src/asc/__init__.py` via `pyproject.toml` dynamic attr | Single owner — healthy |
| Product-type kind sets | `sales.py` `FIRST_TIME`/`REDOWNLOAD`/`UPDATE` | Single owner — healthy. `cli.py:20` unused import of `FIRST_TIME` (ruff F401) |
| HTTP base URL | `client.py:15` `API_BASE` | Single owner — healthy |
| Credential *runtime* | `~/.appstoreconnect/config.json` + `.p8` | Off-repo, correct |
| Credential *examples* | README, AGENTS, `AGENT_HELP`, `auth` docstring, bullseye | ENT-003 |
| Credential *schemas* | keys-map / flat / legacy | ENT-004 |
| `--json` contract | README + `AGENT_HELP` vs argparse parent flags | ENT-001 (already drifted) |
| "tests pass" | `make test` vs `make bullseye` vs 🎯T1 vs no CI | ENT-002, ENT-007 |
| 🎯T1 status | local `achieved` vs `origin/master` `identified` | git divergence, not duplicate code |

Deliberate duplication: human vs `--json` output in `cli.py` is two renderers of one in-memory row list, not two domain truths.

## Healthy structure worth retaining

- **Acyclic module DAG** with a single HTTP adapter (`Client`) and a single JWT mint (`Credentials.token`). Import graph from AST: `__main__→cli`; `cli→apps,auth,client,reviews,sales`; `apps/reviews/sales→client`; `client→auth`; `auth` has no in-package imports.
- **Secrets stay off-repo.** `.gitignore` covers egg-info/pyc; grep found no `BEGIN` keys. GitHub secret scanning and push protection enabled. This host: `config.json` and both `.p8` files mode `600`.
- **Sales kind mapping is one property** (`SaleRow.kind`) used by `filter_rows` and the CLI default `frozenset({"download"})`. Parse test locks 1F → download (2 units) vs 7F → update (5 units).
- **Injected `requests.Session`** (`client.py:31-33`) is the right seam for hermetic HTTP tests (unused today).
- **404 → empty day** for missing sales reports (`sales.py:128-130`) matches Apple's lag; live `-d 7` completed with a `total` line.
- **Apache-2.0 LICENSE**, `requires-python >=3.10`, console-script entry, `--help-agent` as an agent surface (content needs ENT-001/003 fixes, mechanism is right).
- **🎯T1 written as assertions**, including "nothing secret is committed" — that bullet still holds.

## Hygiene posture

`hygiene.yaml` is **absent**. Posture is **not declared**. It was not initialized.

Validator invocation from repo root:

```
/Users/marcelo/.claude/skills/hygiene/hygiene_check.py
```

Full output:

```
Traceback (most recent call last):
  File "/Users/marcelo/.claude/skills/hygiene/hygiene_check.py", line 331, in <module>
    sys.exit(main())
             ~~~~^^
  File "/Users/marcelo/.claude/skills/hygiene/hygiene_check.py", line 283, in main
    rep = check_repo(root, doc_path)
  File "/Users/marcelo/.claude/skills/hygiene/hygiene_check.py", line 237, in check_repo
    doc = yaml.safe_load(doc_path.read_text())
                         ~~~~~~~~~~~~~~~~~~^^
  …
FileNotFoundError: [Errno 2] No such file or directory: '/Users/marcelo/work/github.com/marcelocantos/asc/hygiene.yaml'
```

Exit status: 1.

Held tiers / floors: n/a (no declaration). Drift: n/a. Planned/skipped gaps: n/a.

Overlap: ENT-002/ENT-005/ENT-007 are the missing controls a future `hygiene.yaml` would declare (`correctness` tests, `build` CI, `deps` alerts). Do not encode them until the owner onboards hygiene.

Entropy findings suitable for later hygiene enforcement: ENT-001 parser tests (`command: pytest`), ENT-005 CI job + vulnerability alerts, ENT-003 help-text placeholders (`file` regex).

## Oracle coverage and residue

| Property | Decision path |
|---|---|
| TSV parse + download/update kind filter | Shipped hermetic test `test_parse_and_filter_downloads` — green this audit |
| CLI argparse contract (`--json`/`--key` placement, README examples) | **Nothing standing.** This audit's live/auxiliary matrix found ENT-001 |
| JWT mint / `load_credentials` shapes | **Nothing.** Live `whoami` exit 0 on this host only |
| HTTP 200/404/4xx + gzip sales body | **Nothing hermetic.** Live human `sales -d 7` exit 0 this audit; 404-empty-day untested |
| `asc apps` / `asc reviews` JSON:API mapping | **Nothing hermetic.** Prefix `--json` `apps` exit 0 (19 apps) this audit |
| Owner-visible journey `asc sales --app MultiMaze -d 30` | One-time 🎯T1 attestation (2026-07-21). Not wired. Re-run this audit with `-d 7` human table, exit 0 |
| Credentials not committed | Convention + git grep + GitHub secret scanning. No automated `absent:` check |
| Dependency vulnerabilities | **Nothing.** Alerts disabled; pip-audit not installed |
| Import cycles / architecture | This audit's AST graph. No Arch test |
| ruff F401 | Auxiliary ruff, not in CI |
| `make bullseye` dirty tree | Local; currently red due to user-owned untracked dir |

Failed/skipped checks: `make bullseye` exit 2 (dirty tree, not product); `hygiene_check.py` exit 1 (undeclared); ruff exit 1 (F401); pip-audit/mypy/jscpd/pytest-cov unavailable (not installed).

**Owner residue** (intent, not mechanical follow-up):

- Keep Squz key ids in shipped `--help-agent`, or placeholder them (ENT-003)?
- Retain legacy `api_key.json` / inline PEM (ENT-004)?
- Accept no live CI journey because Apple credentials cannot live in GitHub, or add a manual/periodic cadence?

## Remediation sequence

1. **Repair the CLI contract (ENT-001).** Register `--json`/`--key` on subparsers; add `parse_args` tests that include README's suffix form. This is the enforcement seam.
2. **Hermetic auth + Client tests (ENT-002, ENT-004).** Tmp config + fake session. Do not delete legacy loaders until a test proves zero callers or the owner drops them.
3. **Disambiguate `find_app` (ENT-006)** while adding app-list fixtures.
4. **CI pytest on `master` (ENT-002, ENT-005).** Enable vulnerability alerts. Optionally `uv lock`. Point `make bullseye` at `test` (ENT-007) or stop treating it as a correctness gate.
5. **Converge help/identity copies (ENT-003)** only after the parser tests freeze the example command strings.
6. **Declare `hygiene.yaml` when asked** — floors that match reality (tests present; CI/lockfile/alerts planned). Do not ratchet in this audit.
7. Re-run this audit on the same definitions (parser matrix, test file count by module, `gh` workflow list, presence/absence of `hygiene.yaml`).

No architectural rewrite is required. The DAG is the shape to keep.

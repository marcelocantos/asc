# Copyright 2026 Marcelo Cantos
# SPDX-License-Identifier: Apache-2.0

"""Load App Store Connect credentials and mint JWTs.

Config lives under ``~/.appstoreconnect/`` (never committed):

* ``config.json`` — preferred multi-key layout::

      {
        "issuer_id": "<uuid>",
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

* ``api_key.json`` — legacy flat shape (key embedded or path-based) still
  accepted for ship/match tools.

Sales/finance reports need a key with **Sales**, **Finance**, or **Admin**
access. App Manager is enough for apps/reviews/builds, not salesReports.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import jwt

CONFIG_DIR = Path.home() / ".appstoreconnect"
CONFIG_PATH = CONFIG_DIR / "config.json"
LEGACY_API_KEY_PATH = CONFIG_DIR / "api_key.json"
PRIVATE_KEYS_DIR = CONFIG_DIR / "private_keys"

# Apple caps JWT lifetime at 20 minutes.
_TOKEN_TTL_S = 19 * 60


@dataclass(frozen=True)
class Credentials:
    """Resolved key material for one ASC API call."""

    issuer_id: str
    key_id: str
    key_pem: str
    vendor_number: str | None = None
    key_name: str | None = None
    access: tuple[str, ...] = ()

    def token(self) -> str:
        """Mint a short-lived ES256 JWT for ``Authorization: Bearer``."""
        now = int(time.time())
        return jwt.encode(
            {
                "iss": self.issuer_id,
                "iat": now,
                "exp": now + _TOKEN_TTL_S,
                "aud": "appstoreconnect-v1",
            },
            self.key_pem,
            algorithm="ES256",
            headers={"alg": "ES256", "kid": self.key_id, "typ": "JWT"},
        )


class ConfigError(RuntimeError):
    """Missing or malformed credentials under ``~/.appstoreconnect``."""


def _expand(path: str | Path) -> Path:
    return Path(os.path.expanduser(str(path))).resolve()


def _read_pem(path: Path) -> str:
    if not path.is_file():
        raise ConfigError(f"private key not found: {path}")
    return path.read_text()


def load_credentials(key: str | None = None) -> Credentials:
    """Resolve credentials.

    ``key`` selects a named entry from ``config.json``'s ``keys`` map
    (e.g. ``ops``, ``fastlane``). When omitted, uses ``default_key`` or
    the sole entry, falling back to legacy ``api_key.json``.
    """
    if CONFIG_PATH.is_file():
        return _from_config(json.loads(CONFIG_PATH.read_text()), key)
    if LEGACY_API_KEY_PATH.is_file():
        return _from_legacy(json.loads(LEGACY_API_KEY_PATH.read_text()))
    raise ConfigError(
        f"no credentials at {CONFIG_PATH} or {LEGACY_API_KEY_PATH}; "
        "see `asc --help-agent`"
    )


def _from_config(raw: dict, key: str | None) -> Credentials:
    issuer = raw.get("issuer_id")
    if not issuer:
        raise ConfigError(f"{CONFIG_PATH}: missing issuer_id")

    vendor = raw.get("vendor_number")
    keys = raw.get("keys") or {}

    if keys:
        name = key or raw.get("default_key")
        if name is None and len(keys) == 1:
            name = next(iter(keys))
        if not name or name not in keys:
            available = ", ".join(sorted(keys)) or "(none)"
            raise ConfigError(
                f"unknown key {name!r}; available: {available}"
            )
        entry = keys[name]
        key_id = entry.get("key_id")
        path = entry.get("path") or str(PRIVATE_KEYS_DIR / f"AuthKey_{key_id}.p8")
        if not key_id:
            raise ConfigError(f"{CONFIG_PATH}: keys.{name}.key_id missing")
        pem = _read_pem(_expand(path))
        access = tuple(entry.get("access") or ())
        return Credentials(
            issuer_id=issuer,
            key_id=key_id,
            key_pem=pem,
            vendor_number=vendor,
            key_name=name,
            access=access,
        )

    # Flat config.json (no keys map)
    key_id = raw.get("key_id")
    if not key_id:
        raise ConfigError(f"{CONFIG_PATH}: missing key_id")
    path = raw.get("key_path") or str(PRIVATE_KEYS_DIR / f"AuthKey_{key_id}.p8")
    if "key" in raw and not Path(path).is_file():
        pem = raw["key"]
    else:
        pem = _read_pem(_expand(path))
    return Credentials(
        issuer_id=issuer,
        key_id=key_id,
        key_pem=pem,
        vendor_number=vendor,
        key_name=key,
    )


def _from_legacy(raw: dict) -> Credentials:
    issuer = raw.get("issuer_id")
    key_id = raw.get("key_id")
    if not issuer or not key_id:
        raise ConfigError(f"{LEGACY_API_KEY_PATH}: need issuer_id + key_id")
    if "key" in raw:
        pem = raw["key"]
    else:
        path = raw.get("key_path") or str(PRIVATE_KEYS_DIR / f"AuthKey_{key_id}.p8")
        pem = _read_pem(_expand(path))
    return Credentials(
        issuer_id=issuer,
        key_id=key_id,
        key_pem=pem,
        vendor_number=raw.get("vendor_number"),
        key_name="legacy",
    )

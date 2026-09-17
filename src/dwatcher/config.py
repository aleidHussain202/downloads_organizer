"""TOML config loading with defaults (stdlib tomllib)."""

from __future__ import annotations

from pathlib import Path

import tomllib


DEFAULTS = {
    "watch_dir": Path.home() / "Downloads",
    "dest_root": None,  # defaults to watch_dir itself
    "interval": 10,
    "quiet_seconds": 30,
    "dry_run": False,
    "rules": {},
}


def load_config(path) -> dict:
    """Load config from a TOML file, falling back to DEFAULTS.

    [watch] table holds settings; [rules] maps extensions to categories.
    """
    cfg = dict(DEFAULTS)
    p = Path(path)
    if not p.exists():
        return cfg

    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid config file {p}: {exc}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot read config file {p}: {exc}") from exc
    watch = data.get("watch", {})
    if "dir" in watch:
        cfg["watch_dir"] = Path(watch["dir"])
    if "dest" in watch:
        raw = watch["dest"]
        cfg["dest_root"] = None if (raw is None or str(raw) == "") else Path(raw)
    for key in ("interval", "quiet_seconds"):
        if key in watch:
            try:
                cfg[key] = int(watch[key])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid config {key}={watch[key]!r}: must be int") from exc
            if cfg[key] < 0:
                raise ValueError(f"invalid config {key}={cfg[key]}: must be >= 0")
    if "dry_run" in watch:
        cfg["dry_run"] = bool(watch["dry_run"])
    raw_rules = data.get("rules", {})
    if not isinstance(raw_rules, dict):
        raise ValueError("invalid config [rules]: must be a table")
    cfg["rules"] = dict(raw_rules)
    return cfg

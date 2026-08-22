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

    watch = data.get("watch", {})
    if "dir" in watch:
        cfg["watch_dir"] = Path(watch["dir"])
    if "dest" in watch:
        cfg["dest_root"] = Path(watch["dest"])
    for key in ("interval", "quiet_seconds"):
        if key in watch:
            cfg[key] = int(watch[key])
    if "dry_run" in watch:
        cfg["dry_run"] = bool(watch["dry_run"])
    cfg["rules"] = dict(data.get("rules", {}))
    return cfg

"""Command-line interface: once | watch | recover | stats | gui."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load_config
from .recovery import recover_pending
from .scanner import scan_once
from .store import Store
from .watcher import Watcher


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dwatcher",
        description="Watch a folder and auto-organize completed downloads.",
    )
    p.add_argument("--config", default=None, help="path to dwatcher.toml")
    p.add_argument("--version", action="version", version=f"dwatcher {__version__}")
    # no subcommand (e.g. double-clicking the exe) falls through to the GUI
    sub = p.add_subparsers(dest="command")

    once = sub.add_parser("once", help="run a single scan")
    once.add_argument("--watch", default=None)
    once.add_argument("--dest", default=None)
    once.add_argument("--quiet", type=int, default=30,
                      help="seconds of no-change before a file counts as done")
    once.add_argument("--dry-run", action="store_true")
    once.add_argument("--db", default=None)

    watch = sub.add_parser("watch", help="watch continuously")
    watch.add_argument("--watch", dest="watch_dir", default=None)
    watch.add_argument("--dest", default=None)
    watch.add_argument("--interval", type=int, default=10)
    watch.add_argument("--quiet", type=int, default=30)
    watch.add_argument("--dry-run", action="store_true")
    watch.add_argument("--db", default=None)
    watch.add_argument("--log", default=None)

    rec = sub.add_parser("recover", help="resolve interrupted moves from journal")
    rec.add_argument("--db", default=None)

    st = sub.add_parser("stats", help="show move counts per category")
    st.add_argument("--db", default=None)

    gui = sub.add_parser("gui", help="launch native desktop GUI")
    gui.add_argument("--config", default=None, help="path to dwatcher.toml")
    return p


def _resolve_settings(args) -> dict:
    cfg = load_config(args.config or "dwatcher.toml")
    watch_override = getattr(args, "watch", None) or getattr(args, "watch_dir", None)
    if watch_override:
        cfg["watch_dir"] = Path(watch_override)
    if getattr(args, "dest", None):
        cfg["dest_root"] = Path(args.dest)
    for attr, key in (("quiet", "quiet_seconds"), ("interval", "interval")):
        val = getattr(args, attr, None)
        if val is not None:
            if int(val) < 0:
                raise SystemExit(f"error: --{attr} must be >= 0")
            cfg[key] = int(val)
    if getattr(args, "dry_run", False):
        cfg["dry_run"] = True
    if cfg.get("dest_root") is None:
        cfg["dest_root"] = cfg["watch_dir"]
    return cfg


def _db_path(args, config_path=None) -> Path:
    raw = getattr(args, "db", None)
    if raw:
        p = Path(raw)
        if not p.is_absolute() and config_path:
            return Path(config_path).parent / p
        return p
    base = Path(config_path).parent if config_path else Path.cwd()
    return base / "dwatcher.db"


def _log_path(args, config_path=None) -> Path:
    raw = getattr(args, "log", None)
    if raw:
        p = Path(raw)
        if not p.is_absolute() and config_path:
            return Path(config_path).parent / p
        return p
    base = Path(config_path).parent if config_path else Path.cwd()
    return base / "dwatcher_events.jsonl"


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.command in ("once", "watch"):
        cfg = _resolve_settings(args)

        store = Store(_db_path(args, args.config))
        try:
            if args.command == "once":
                report = scan_once(
                    cfg["watch_dir"], cfg["dest_root"],
                    rules=cfg.get("rules") or None,
                    quiet_seconds=cfg["quiet_seconds"],
                    dry_run=cfg["dry_run"],
                    store=store,
                )
                if report.errors and not report.moved:
                    print(f"error: cannot read {cfg['watch_dir']}")
                    return 1
                state = "would move" if cfg["dry_run"] else "moved"
                print(f"{state}: {len(report.moved)} file(s), "
                      f"scanned: {report.scanned}, errors: {report.errors}")
                for res in report.moved:
                    print(f"  {res.src} -> {res.dst}")
                return 0

            watcher = Watcher(
                cfg["watch_dir"], cfg["dest_root"],
                interval=cfg["interval"], quiet_seconds=cfg["quiet_seconds"],
                dry_run=cfg["dry_run"], rules=cfg.get("rules") or None,
                store=store, log_path=_log_path(args, args.config),
            )
            def _announce(report):
                if report is not None and report.moved:
                    for res in report.moved:
                        print(f"moved: {res.src} -> {res.dst}", flush=True)
            watcher.on_scan = _announce
            print(f"watching {cfg['watch_dir']} every {cfg['interval']}s "
                  f"(Ctrl+C to stop)", flush=True)
            try:
                watcher.run()
            except KeyboardInterrupt:
                print("\nstopped")
            return 0
        finally:
            store.close()

    elif args.command == "recover":
        store = Store(_db_path(args, args.config))
        try:
            actions = recover_pending(store)
            if not actions:
                print("journal clean; nothing to recover")
            for a in actions:
                print(a)
            return 0
        finally:
            store.close()

    elif args.command == "stats":
        store = Store(_db_path(args, args.config))
        try:
            rows = store.stats_by_category()
            total = sum(n for _, n in rows)
            print(f"total real moves: {total}")
            for cat, n in rows:
                print(f"  {cat:<12} {n}")
            return 0
        finally:
            store.close()

    if args.command in (None, "gui"):
        from .gui import main as gui_main
        gui_main(args.config)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

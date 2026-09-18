"""Continuous watch loop with backoff + JSONL structured logging."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


class Watcher:
    def __init__(
        self,
        watch_dir,
        dest_root,
        interval: int = 10,
        quiet_seconds: int = 30,
        dry_run: bool = False,
        rules: dict | None = None,
        store=None,
        log_path=None,
        clock=None,
        on_scan=None,
        max_backoff: int = 60,
        log_max_bytes: int = 1_000_000,
    ):
        self.watch_dir = watch_dir
        self.dest_root = dest_root
        self.interval = interval
        self.quiet_seconds = quiet_seconds
        self.dry_run = dry_run
        self.rules = rules
        self.store = store
        self.log_path = log_path
        self.clock = clock or time
        self.on_scan = on_scan  # test seam / metrics hook
        self.max_backoff = max_backoff
        self.log_max_bytes = log_max_bytes
        self._on_error = None   # test seam to force errors
        self.previous_sizes: dict = {}

    # -- logging ----------------------------------------------------------

    def _log(self, event: str, **fields):
        if self.log_path is None:
            return
        try:
            p = Path(self.log_path)
            if p.exists() and p.stat().st_size > self.log_max_bytes:
                try:
                    p.replace(p.with_suffix(".jsonl.1"))
                except OSError:
                    pass
            rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event}
            rec.update(fields)
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        except OSError:
            pass  # logging must never fail a scan

    # -- scanning ---------------------------------------------------------

    def scan_once(self):
        from .scanner import scan_once
        report = scan_once(self.watch_dir, self.dest_root, rules=self.rules,
            quiet_seconds=self.quiet_seconds, dry_run=self.dry_run,
            store=self.store, previous_sizes=self.previous_sizes)
        for res in report.moved:
            try:
                cat = Path(res.dst).parent.name
            except Exception:
                cat = "Unknown"
            self._log("moved", src=str(res.src), dst=str(res.dst), category=cat)
        for note in report.notes:
            self._log("note", message=note)
        return report

    def scan_once_safe(self):
        """Scan that never raises; logs errors instead (Layer 12).

        A failing on_scan hook counts as a failed cycle (triggers
        backoff). Returns (ok, result).
        """
        try:
            if self._on_error is not None:
                raise OSError("forced")
            report = self.scan_once()
            if self.on_scan is not None:
                self.on_scan(report)
            return True, report
        except Exception as exc:  # noqa: BLE001 - watcher must survive
            self._log("error", error=str(exc))
            return False, None

    def _sleep(self, seconds):
        self.clock.sleep(seconds)

    def run(self, max_cycles: int | None = None):
        """Loop until stopped. Backs off after repeated failures.

        First failure sleeps just `interval`; each additional
        consecutive failure doubles it, capped at max_backoff.
        Any success resets the backoff.
        """
        cycles = 0
        consecutive_fails = 0
        while max_cycles is None or cycles < max_cycles:
            ok, report = self.scan_once_safe()
            moved = len(getattr(report, "moved", None) or [])
            self._log("scan", ok=ok, moved=moved)
            cycles += 1
            if ok:
                consecutive_fails = 0
                delay = float(self.interval)
            else:
                consecutive_fails += 1
                delay = min(
                    float(self.interval) * (2 ** (consecutive_fails - 1)),
                    float(self.max_backoff),
                )
            self._sleep(delay)

from __future__ import annotations
import queue
import threading
import time
from pathlib import Path
from .watcher import Watcher


class WatcherThread(threading.Thread):
    def __init__(self, state, ui_queue: queue.Queue, store):
        super().__init__(daemon=True)
        self.state = state
        self.ui_queue = ui_queue
        self.store = store
        self.watcher = Watcher(watch_dir=state.watch_dir, dest_root=state.dest_root,
                               interval=state.interval, quiet_seconds=state.quiet_seconds,
                               dry_run=state.dry_run, rules=state.rules, store=self.store,
                               log_path=Path("dwatcher_events.jsonl"))

    def run(self):
        consecutive_fails = 0
        while self.state.running:
            if not self.state.paused:
                ok, report = self.watcher.scan_once_safe()
                moved = len(getattr(report, "moved", None) or []) if report else 0
                self.ui_queue.put(("scan_result", ok, moved))
                consecutive_fails = 0 if ok else consecutive_fails + 1
                delay = float(self.state.interval) if ok else min(
                    float(self.state.interval) * (2 ** (consecutive_fails - 1)),
                    float(self.watcher.max_backoff))
            else:
                delay = 1.0
            time.sleep(delay)

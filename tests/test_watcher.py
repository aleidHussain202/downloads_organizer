"""Tests for dwatcher.watcher — continuous watch loop + JSONL logging."""
import json
import time

import pytest

from dwatcher.watcher import Watcher


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def time(self):
        return self.t

    def sleep(self, s):
        self.t += s


class TestWatcherLoop:
    def test_runs_scans_until_stopped(self, tmp_path):
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        clock = FakeClock()
        scans = []

        watcher = Watcher(w, d, interval=5, clock=clock,
                          on_scan=scans.append)
        watcher.run(max_cycles=3)
        assert len(scans) == 3
        assert clock.t == 1000.0 + 3 * 5   # slept between scans

    def test_backoff_after_repeated_errors(self, tmp_path):
        """A failing scan doubles the sleep, capped at max_backoff."""
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        clock = FakeClock()

        def failing_scan(*a, **k):
            raise OSError("disk gone")

        watcher = Watcher(w, d, interval=10, clock=clock,
                          on_scan=failing_scan, max_backoff=60)
        watcher.run(max_cycles=4)
        # sleeps: 10, 20, 40, 60(cap) = 130 total after cycle starts
        assert clock.t == 1000.0 + 10 + 20 + 40 + 60

    def test_backoff_resets_on_success(self, tmp_path):
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        clock = FakeClock()
        calls = {"n": 0}

        def flaky_scan(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("boom")

        watcher = Watcher(w, d, interval=10, clock=clock,
                          on_scan=flaky_scan)
        watcher.run(max_cycles=3)
        # fail(10), success(10 reset), success(10)
        assert clock.t == 1000.0 + 30

    def test_jsonl_events_logged(self, tmp_path):
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        old = time.time() - 300
        f = w / "a.zip"; f.write_bytes(b"x")
        import os; os.utime(f, (old, old))
        logf = tmp_path / "events.jsonl"

        watcher = Watcher(w, d, log_path=logf)
        watcher.scan_once()

        lines = [json.loads(l) for l in logf.read_text().splitlines()]
        moved_events = [e for e in lines if e["event"] == "moved"]
        assert len(moved_events) == 1
        assert moved_events[0]["category"] == "Archives"
        assert "ts" in moved_events[0]

    def test_error_event_logged(self, tmp_path):
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        logf = tmp_path / "events.jsonl"
        watcher = Watcher(w, d, log_path=logf)

        def boom(*a, **k):
            raise OSError("nope")

        watcher._on_error = boom
        watcher.scan_once_safe()
        lines = [json.loads(l) for l in logf.read_text().splitlines()]
        assert any(e["event"] == "error" for e in lines)


def test_log_failure_does_not_fail_scan(tmp_path):
    import os, time
    from dwatcher.watcher import Watcher
    watch = tmp_path / "w"; watch.mkdir()
    dest = tmp_path / "d"; dest.mkdir()
    f = watch / "doc.pdf"
    f.write_bytes(b"x" * 10)
    old = time.time() - 300
    os.utime(f, (old, old))
    bad_log = tmp_path / "nodir" / "e.jsonl"
    w = Watcher(watch, dest, interval=0, quiet_seconds=0, log_path=bad_log)
    ok, report = w.scan_once_safe()
    assert ok is True
    assert len(report.moved) == 1


def test_previous_sizes_tracked(tmp_path):
    from dwatcher.watcher import Watcher
    watch = tmp_path / "w2"; watch.mkdir()
    dest = tmp_path / "d2"; dest.mkdir()
    w = Watcher(watch, dest, interval=0, quiet_seconds=0)
    w.scan_once()
    assert isinstance(w.previous_sizes, dict)

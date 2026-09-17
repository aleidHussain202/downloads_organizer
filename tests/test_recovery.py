"""Tests for crash-safe moves + recovery."""
import time

import pytest

from dwatcher.recovery import recover_pending
from dwatcher.scanner import scan_once


class TestScanWritesJournal:
    def test_intent_cleared_after_successful_move(self, tmp_path):
        from dwatcher.store import Store
        watch = tmp_path / "w"; watch.mkdir()
        dest = tmp_path / "s"; dest.mkdir()
        old = time.time() - 300
        f = watch / "a.zip"; f.write_bytes(b"x")
        import os; os.utime(f, (old, old))
        store = Store(tmp_path / "h.db")
        scan_once(watch, dest, store=store)
        assert store.pending_intents() == []
        store.close()

    def test_dry_run_leaves_no_intents(self, tmp_path):
        from dwatcher.store import Store
        watch = tmp_path / "w"; watch.mkdir()
        dest = tmp_path / "s"; dest.mkdir()
        old = time.time() - 300
        f = watch / "a.zip"; f.write_bytes(b"x")
        import os; os.utime(f, (old, old))
        store = Store(tmp_path / "h.db")
        scan_once(watch, dest, dry_run=True, store=store)
        assert store.pending_intents() == []
        store.close()


class TestRecover:
    def test_completes_interrupted_move(self, tmp_path):
        """Process died after moving but before clearing intent:
        src gone, dst exists -> just clear.
        """
        from dwatcher.store import Store
        dest = tmp_path / "s"
        moved = dest / "Archives"; moved.mkdir(parents=True)
        (moved / "a.zip").write_bytes(b"x")
        store = Store(tmp_path / "h.db")
        store.write_intent(tmp_path / "w" / "a.zip", moved / "a.zip")
        actions = recover_pending(store)
        assert any("cleared" in a for a in actions)
        assert store.pending_intents() == []
        store.close()

    def test_redoes_never_started_move(self, tmp_path):
        """src still exists, dst missing -> perform the move now."""
        from dwatcher.store import Store
        src = tmp_path / "w" / "a.zip"
        src.parent.mkdir(parents=True)
        src.write_bytes(b"data")
        dst = tmp_path / "s" / "Archives" / "a.zip"
        store = Store(tmp_path / "h.db")
        store.write_intent(src, dst)
        actions = recover_pending(store)
        assert dst.exists()
        assert not src.exists()
        assert any("moved" in a for a in actions)
        store.close()

    def test_reports_missing_both(self, tmp_path):
        from dwatcher.store import Store
        store = Store(tmp_path / "h.db")
        store.write_intent(tmp_path / "gone1", tmp_path / "gone2")
        actions = recover_pending(store)
        assert any("missing" in a.lower() for a in actions)
        store.close()


def test_both_present_different_size_keeps_both(tmp_path):
    from dwatcher.store import Store
    from dwatcher.recovery import recover_pending
    src = tmp_path / "a.pdf"; dst = tmp_path / "out" / "a.pdf"
    dst.parent.mkdir()
    src.write_bytes(b"x" * 10); dst.write_bytes(b"y" * 99)
    s = Store(tmp_path / "r.db")
    try:
        s.write_intent(str(src), str(dst))
        actions = recover_pending(s)
        assert src.exists() or (dst.parent / "a (1).pdf").exists()
        assert dst.read_bytes() == b"y" * 99
    finally:
        s.close()


def test_locked_src_does_not_abort_rest(tmp_path, monkeypatch):
    import shutil
    from dwatcher.store import Store
    from dwatcher.recovery import recover_pending
    a = tmp_path / "a.pdf"; b = tmp_path / "b.pdf"
    a.write_bytes(b"a"); b.write_bytes(b"b")
    s = Store(tmp_path / "r2.db")
    try:
        s.write_intent(str(a), str(tmp_path / "o1" / "a.pdf"))
        s.write_intent(str(b), str(tmp_path / "o2" / "b.pdf"))
        orig = shutil.move
        def flaky(s_, d_):
            if str(s_).endswith("a.pdf"): raise OSError("locked")
            return orig(s_, d_)
        monkeypatch.setattr(shutil, "move", flaky)
        actions = recover_pending(s)
        assert any("locked" in x or "could not" in x for x in actions)
        assert (tmp_path / "o2" / "b.pdf").exists()
    finally:
        s.close()

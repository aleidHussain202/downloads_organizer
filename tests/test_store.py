"""Tests for dwatcher.store — SQLite history + write-ahead intent journal."""
import sqlite3

import pytest

from dwatcher.store import Store


@pytest.fixture()
def store(tmp_path):
    s = Store(tmp_path / "history.db")
    yield s
    s.close()


class TestHistory:
    def test_record_and_fetch(self, store):
        store.record_move(src="C:/d/a.zip", dst="C:/s/Archives/a.zip",
                          category="Archives", size=123, dry_run=False)
        rows = store.recent_moves(limit=10)
        assert len(rows) == 1
        assert rows[0]["category"] == "Archives"
        assert rows[0]["size"] == 123

    def test_dry_run_marked_not_moved(self, store):
        store.record_move("a", "b", "X", 1, dry_run=True)
        assert store.recent_moves()[0]["dry_run"] == 1

    def test_recent_limit(self, store):
        for i in range(15):
            store.record_move(f"{i}", f"d{i}", "X", i, dry_run=False)
        assert len(store.recent_moves(limit=5)) == 5

    def test_survives_reopen(self, tmp_path):
        db = tmp_path / "h.db"
        s1 = Store(db)
        s1.record_move("a", "b", "X", 1, dry_run=False)
        s1.close()
        s2 = Store(db)
        assert len(s2.recent_moves()) == 1
        s2.close()


class TestJournal:
    """Write-ahead intent: written BEFORE a move, cleared AFTER success.

    If the process dies mid-move, `pending_intents()` knows what to fix.
    """

    def test_intent_roundtrip(self, store):
        store.write_intent("C:/d/a.zip", "C:/s/Archives/a.zip")
        pend = store.pending_intents()
        assert pend == [("C:/d/a.zip", "C:/s/Archives/a.zip")]
        store.clear_intent("C:/s/Archives/a.zip")
        assert store.pending_intents() == []

    def test_multiple_pending_kept_in_order(self, store):
        store.write_intent("s1", "d1")
        store.write_intent("s2", "d2")
        assert store.pending_intents() == [("s1", "d1"), ("s2", "d2")]


class TestStats:
    def test_counts_by_category(self, store):
        store.record_move("a", "b", "Archives", 10, dry_run=False)
        store.record_move("c", "d", "Archives", 20, dry_run=False)
        store.record_move("e", "f", "Images", 30, dry_run=False)
        stats = dict(store.stats_by_category())
        assert stats["Archives"] == 2
        assert stats["Images"] == 1

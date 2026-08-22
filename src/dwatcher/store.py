"""SQLite persistence: move history, write-ahead intent journal, stats."""

from __future__ import annotations

import sqlite3


class Store:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL DEFAULT (datetime('now')),
                src TEXT NOT NULL,
                dst TEXT NOT NULL,
                category TEXT NOT NULL,
                size INTEGER NOT NULL,
                dry_run INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS intents (
                dst TEXT PRIMARY KEY,
                src TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_moves_ts ON moves(ts);
            """
        )
        self.conn.commit()

    # -- history ----------------------------------------------------------

    def record_move(self, src, dst, category, size, dry_run):
        self.conn.execute(
            "INSERT INTO moves (src, dst, category, size, dry_run) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(src), str(dst), category, int(size), 1 if dry_run else 0),
        )
        self.conn.commit()

    def recent_moves(self, limit: int = 20):
        cur = self.conn.execute(
            "SELECT * FROM moves ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in cur.fetchall()]

    def stats_by_category(self):
        cur = self.conn.execute(
            "SELECT category, COUNT(*) AS n FROM moves "
            "WHERE dry_run = 0 GROUP BY category ORDER BY n DESC"
        )
        return [(r["category"], r["n"]) for r in cur.fetchall()]

    # -- write-ahead intent journal ----------------------------------------

    def write_intent(self, src, dst):
        self.conn.execute(
            "INSERT OR REPLACE INTO intents (dst, src) VALUES (?, ?)",
            (str(dst), str(src)),
        )
        self.conn.commit()

    def pending_intents(self):
        cur = self.conn.execute(
            "SELECT src, dst FROM intents ORDER BY rowid"
        )
        return [(r["src"], r["dst"]) for r in cur.fetchall()]

    def clear_intent(self, dst):
        self.conn.execute("DELETE FROM intents WHERE dst = ?", (str(dst),))
        self.conn.commit()

    def close(self):
        self.conn.close()

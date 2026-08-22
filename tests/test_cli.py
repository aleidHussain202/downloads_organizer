"""Tests for dwatcher.cli — command dispatch."""
import json
import os
import time

import pytest

from dwatcher.cli import build_parser, main


class TestParser:
    def test_once_command_parses(self):
        ns = build_parser().parse_args(["once", "--watch", "C:/d", "--dest", "C:/s"])
        assert ns.command == "once"
        assert str(ns.watch) == "C:/d"

    def test_watch_defaults_interval(self):
        ns = build_parser().parse_args(["watch"])
        assert ns.interval == 10

    def test_dry_run_flag(self):
        ns = build_parser().parse_args(["once", "--dry-run"])
        assert ns.dry_run is True


class TestMainOnce:
    def test_once_moves_files_and_prints_report(self, tmp_path, capsys):
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        old = time.time() - 300
        f = w / "a.zip"; f.write_bytes(b"x")
        os.utime(f, (old, old))
        rc = main(["once", "--watch", str(w), "--dest", str(d)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "moved" in out.lower()
        assert not f.exists()
        assert (d / "Archives" / "a.zip").exists()

    def test_once_dry_run_touches_nothing(self, tmp_path, capsys):
        w = tmp_path / "w"; w.mkdir()
        d = tmp_path / "s"; d.mkdir()
        old = time.time() - 300
        f = w / "a.pdf"; f.write_bytes(b"x")
        os.utime(f, (old, old))
        rc = main(["once", "--watch", str(w), "--dest", str(d), "--dry-run"])
        assert rc == 0
        assert f.exists()

    def test_missing_watch_dir_errors_cleanly(self, tmp_path, capsys):
        rc = main(["once", "--watch", str(tmp_path / "nope")])
        assert rc == 1
        assert "error" in capsys.readouterr().out.lower()


class TestRecoverAndStats:
    def test_recover_reports_actions(self, tmp_path, capsys):
        from dwatcher.store import Store
        store = Store(tmp_path / "h.db")
        store.write_intent(str(tmp_path / "gone"), str(tmp_path / "gone2"))
        store.close()
        rc = main(["recover", "--db", str(tmp_path / "h.db")])
        assert rc == 0
        assert "missing" in capsys.readouterr().out.lower()

    def test_stats_prints_categories(self, tmp_path, capsys):
        from dwatcher.store import Store
        store = Store(tmp_path / "h.db")
        store.record_move("a", "b", "Images", 5, dry_run=False)
        store.close()
        rc = main(["stats", "--db", str(tmp_path / "h.db")])
        assert rc == 0
        assert "Images" in capsys.readouterr().out


class TestInPlaceMode:
    """No recursion -> dest inside watch dir is safe and is the default:
    Downloads/Installers, Downloads/Documents, ..."""

    def test_default_dest_is_watch_dir_itself(self, tmp_path, capsys):
        w = tmp_path / "w"; w.mkdir()
        old = time.time() - 300
        f = w / "a.zip"; f.write_bytes(b"x")
        os.utime(f, (old, old))
        rc = main(["once", "--watch", str(w)])
        assert rc == 0
        assert (w / "Installers" / "a.zip").exists()

    def test_category_folders_not_rescanned_as_files(self, tmp_path):
        w = tmp_path / "w"; w.mkdir()
        (w / "Archives").mkdir()
        old = time.time() - 300
        f = w / "a.zip"; f.write_bytes(b"x")
        os.utime(f, (old, old))
        rc = main(["once", "--watch", str(w)])
        assert rc == 0
        # second run: nothing new to do, existing tree untouched
        capsys.readouterr()
        rc2 = main(["once", "--watch", str(w)])
        assert rc2 == 0
        assert (w / "Archives" / "a.zip").exists()

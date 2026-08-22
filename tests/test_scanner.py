"""Tests for dwatcher.scanner — the once-over pipeline.

scan_once(watch_dir, dest_root, rules, dry_run) -> ScanReport
"""
import time

import pytest

from dwatcher.scanner import scan_once


def mk(path, size=10):
    path.write_bytes(b"x" * size)
    return path


class TestScanOnce:
    def test_organizes_stable_files_by_category(self, tmp_path):
        watch = tmp_path / "watch"; watch.mkdir()
        dest = tmp_path / "sorted"; dest.mkdir()
        old = time.time() - 300
        mk(watch / "setup.exe").touch()
        import os; os.utime(watch / "setup.exe", (old, old))
        report = scan_once(watch, dest)
        assert not (watch / "setup.exe").exists()
        assert (dest / "Installers" / "setup.exe").exists()
        assert len(report.moved) == 1

    def test_skips_partial_downloads(self, tmp_path):
        watch = tmp_path / "watch"; watch.mkdir()
        dest = tmp_path / "sorted"; dest.mkdir()
        mk(watch / "movie.crdownload")
        report = scan_once(watch, dest)
        assert report.moved == []
        assert (watch / "movie.crdownload").exists()

    def test_unclassified_file_left_alone(self, tmp_path):
        watch = tmp_path / "watch"; watch.mkdir()
        dest = tmp_path / "sorted"; dest.mkdir()
        old = time.time() - 300
        f = mk(watch / "weird.xyz")
        import os; os.utime(f, (old, old))
        report = scan_once(watch, dest)
        assert report.moved == []
        assert f.exists()

    def test_dry_run_reports_without_moving(self, tmp_path):
        watch = tmp_path / "watch"; watch.mkdir()
        dest = tmp_path / "sorted"; dest.mkdir()
        old = time.time() - 300
        f = mk(watch / "doc.pdf")
        import os; os.utime(f, (old, old))
        report = scan_once(watch, dest, dry_run=True)
        assert len(report.moved) == 1          # planned
        assert f.exists()                       # untouched
        assert not (dest / "Documents").exists()

    def test_report_counts_scanned(self, tmp_path):
        watch = tmp_path / "watch"; watch.mkdir()
        dest = tmp_path / "sorted"; dest.mkdir()
        mk(watch / "a.zip"); mk(watch / "b.pdf")
        report = scan_once(watch, dest, quiet_seconds=0)
        assert report.scanned == 2

    def test_custom_rules_applied(self, tmp_path):
        watch = tmp_path / "watch"; watch.mkdir()
        dest = tmp_path / "sorted"; dest.mkdir()
        old = time.time() - 300
        f = mk(watch / "model.stl")
        import os; os.utime(f, (old, old))
        report = scan_once(watch, dest, rules={".stl": "3DPrints"})
        assert (dest / "3DPrints" / "model.stl").exists()

    def test_missing_watch_dir_is_error_not_crash(self, tmp_path):
        report = scan_once(tmp_path / "nope", tmp_path / "s")
        assert report.errors >= 1

"""Tests for dwatcher.stability — deciding when a file is a completed download."""
import os
import time

import pytest

from dwatcher.stability import is_stable, is_partial


def touch(path, size=100, mtime=None):
    path.write_bytes(b"x" * size)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


class TestIsPartial:
    def test_crdownload_is_partial(self, tmp_path):
        assert is_partial(tmp_path / "file.crdownload")

    def test_part_is_partial(self, tmp_path):
        assert is_partial(tmp_path / "file.part")

    def test_download_suffix_is_partial(self, tmp_path):
        assert is_partial(tmp_path / "archive.zip.download")

    def test_opdownload_is_partial(self, tmp_path):
        assert is_partial(tmp_path / "file.zip!utQ.opdownload")

    def test_tmp_is_partial(self, tmp_path):
        assert is_partial(tmp_path / "file.tmp")

    def test_normal_file_not_partial(self, tmp_path):
        assert not is_partial(tmp_path / "done.zip")

    def test_partial_marker_does_not_require_existence(self, tmp_path):
        # a file named x.part may not even exist yet; name is enough
        assert is_partial(tmp_path / "x.part")


class TestIsStable:
    def test_missing_file_not_stable(self, tmp_path):
        assert not is_stable(tmp_path / "nope.zip")

    def test_partial_file_not_stable(self, tmp_path):
        f = touch(tmp_path / "movie.crdownload")
        assert not is_stable(f)

    def test_fresh_file_needs_quiet_period(self, tmp_path):
        f = touch(tmp_path / "new.zip")
        # mtime = now -> not quiet long enough
        assert not is_stable(f, quiet_seconds=60)

    def test_old_file_is_stable(self, tmp_path):
        f = touch(tmp_path / "old.zip", mtime=time.time() - 300)
        assert is_stable(f, quiet_seconds=60)

    def test_size_growth_detected_via_snapshot(self, tmp_path):
        f = touch(tmp_path / "growing.zip", mtime=time.time() - 300)
        snap = {f: 50}  # snapshot says it was 50 bytes, now 100 -> changed
        assert not is_stable(f, quiet_seconds=0, previous_sizes=snap)

    def test_size_same_via_snapshot(self, tmp_path):
        f = touch(tmp_path / "same.zip", mtime=time.time() - 300)
        snap = {f: 100}
        assert is_stable(f, quiet_seconds=0, previous_sizes=snap)

    def test_unknown_file_in_snapshot_treated_stable_if_old(self, tmp_path):
        f = touch(tmp_path / "old.zip", mtime=time.time() - 300)
        assert is_stable(f, quiet_seconds=60, previous_sizes={})

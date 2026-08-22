"""Tests for dwatcher.mover — collision-safe file moves with dry-run support."""
import os

import pytest

from dwatcher.mover import plan_move, execute_move


@pytest.fixture()
def sandbox(tmp_path):
    src = tmp_path / "Downloads"
    dst = tmp_path / "Sorted"
    src.mkdir()
    dst.mkdir()
    return src, dst


class TestPlanMove:
    def test_plan_returns_source_and_destination(self, sandbox):
        src, dst = sandbox
        f = src / "a.zip"
        f.write_text("x")
        p = plan_move(f, dst / "Archives")
        assert p.src == f
        assert p.dst == dst / "Archives" / "a.zip"

    def test_plan_is_dry_run_no_files_touched(self, sandbox):
        src, dst = sandbox
        f = src / "a.zip"
        f.write_text("x")
        plan_move(f, dst / "Archives")
        assert f.exists()                      # source untouched
        assert not (dst / "Archives").exists() # nothing created


class TestExecuteMove:
    def test_moves_file_into_category(self, sandbox):
        src, dst = sandbox
        f = src / "a.zip"
        f.write_text("data")
        p = plan_move(f, dst / "Archives")
        result = execute_move(p)
        assert result.ok
        assert not f.exists()
        assert (dst / "Archives" / "a.zip").read_text() == "data"

    def test_collision_gets_numeric_suffix(self, sandbox):
        src, dst = sandbox
        (dst / "Archives").mkdir(parents=True)
        (dst / "Archives" / "a.zip").write_text("old")
        f = src / "a.zip"
        f.write_text("new")
        result = execute_move(plan_move(f, dst / "Archives"))
        assert result.ok
        assert result.dst.name == "a (1).zip"
        assert (dst / "Archives" / "a.zip").read_text() == "old"
        assert result.dst.read_text() == "new"

    def test_double_suffix_collision_increments(self, sandbox):
        src, dst = sandbox
        cat = dst / "Archives"
        cat.mkdir(parents=True)
        (cat / "a.zip").write_text("old")
        (cat / "a (1).zip").write_text("old1")
        f = src / "a.zip"
        f.write_text("new")
        result = execute_move(plan_move(f, cat))
        assert result.dst.name == "a (2).zip"

    def test_missing_source_reports_failure_not_crash(self, sandbox):
        src, dst = sandbox
        p = plan_move(src / "ghost.zip", dst / "Archives")
        result = execute_move(p)
        assert not result.ok
        assert "not found" in result.error.lower()

    def test_dry_run_execute_does_nothing_but_reports(self, sandbox):
        src, dst = sandbox
        f = src / "a.zip"
        f.write_text("x")
        p = plan_move(f, dst / "Archives")
        result = execute_move(p, dry_run=True)
        assert result.ok
        assert f.exists()                       # still there
        assert not (dst / "Archives").exists()  # nothing created

    def test_destination_inside_category_preserved(self, sandbox):
        src, _ = sandbox
        dst = sandbox[1]
        f = src / "a.zip"
        f.write_text("x")
        result = execute_move(plan_move(f, dst / "Archives" / "sub"))
        assert result.dst == dst / "Archives" / "sub" / "a.zip"

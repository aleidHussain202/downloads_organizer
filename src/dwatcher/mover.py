"""Collision-safe file moves with dry-run support."""

from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class MovePlan:
    src: object  # pathlib.Path
    dst: object  # pathlib.Path (final file path, incl. category folder)


@dataclass(frozen=True)
class MoveResult:
    ok: bool
    src: object
    dst: object
    error: str | None = None


def plan_move(src, dest_dir) -> MovePlan:
    """Build a move plan: src file -> dest_dir/<same filename>."""
    return MovePlan(src=src, dst=dest_dir / src.name)


def unique_destination(dst) -> object:
    """Return dst, or dst with ' (n)' inserted before the suffix if taken."""
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    n = 1
    while True:
        candidate = dst.with_name(f"{stem} ({n}){suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def execute_move(plan: MovePlan, dry_run: bool = False) -> MoveResult:
    """Execute a MovePlan. Never raises for expected failure modes."""
    try:
        if not plan.src.exists():
            return MoveResult(False, plan.src, plan.dst,
                              error=f"source not found: {plan.src}")
        final = unique_destination(plan.dst)
        if dry_run:
            # report the destination that WOULD be used (no side effects)
            return MoveResult(True, plan.src, final)
        if not final.parent.exists():
            final.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(plan.src), str(final))
        return MoveResult(True, plan.src, final)
    except OSError as exc:
        return MoveResult(False, plan.src, plan.dst, error=str(exc))

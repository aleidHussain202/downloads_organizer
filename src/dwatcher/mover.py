"""Collision-safe file moves with dry-run support."""
from __future__ import annotations
import shutil
from dataclasses import dataclass
from pathlib import Path
MAX_COLLISIONS = 10000

@dataclass(frozen=True)
class MovePlan:
    src: Path
    dst: Path

@dataclass(frozen=True)
class MoveResult:
    ok: bool
    src: Path
    dst: Path
    error: str | None = None

def plan_move(src: Path, dest_dir: Path) -> MovePlan:
    return MovePlan(src=Path(src), dst=Path(dest_dir) / Path(src).name)

def unique_destination(dst: Path) -> Path:
    dst = Path(dst)
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    for n in range(1, MAX_COLLISIONS + 1):
        candidate = dst.with_name(f"{stem} ({n}){suffix}")
        if not candidate.exists():
            return candidate
    raise OSError(f"too many collisions for {dst}")


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

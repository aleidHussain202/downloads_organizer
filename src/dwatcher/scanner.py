"""The scan pipeline: list -> filter -> classify -> move."""

from __future__ import annotations

from dataclasses import dataclass, field

from .mover import execute_move, plan_move
from .rules import DEFAULT_RULES, classify
from .stability import is_stable


@dataclass
class ScanReport:
    scanned: int = 0
    moved: list = field(default_factory=list)   # MoveResult list
    errors: int = 0
    notes: list = field(default_factory=list)


def scan_once(
    watch_dir,
    dest_root,
    rules: dict | None = None,
    quiet_seconds: int = 30,
    dry_run: bool = False,
) -> ScanReport:
    """One pass over watch_dir. Moves stable, classified files into
    dest_root/<Category>/.
    """
    report = ScanReport()
    try:
        entries = sorted(watch_dir.iterdir())
    except OSError as exc:
        report.errors += 1
        report.notes.append(f"cannot list {watch_dir}: {exc}")
        return report

    active_rules = DEFAULT_RULES if rules is None else rules

    for entry in entries:
        if not entry.is_file():
            continue
        report.scanned += 1
        if not is_stable(entry, quiet_seconds=quiet_seconds):
            continue
        category = classify(entry.name, active_rules)
        if category is None:
            continue
        plan = plan_move(entry, dest_root / category)
        result = execute_move(plan, dry_run=dry_run)
        if result.ok:
            report.moved.append(result)
        else:
            report.errors += 1
            report.notes.append(f"move failed: {result.error}")

    return report

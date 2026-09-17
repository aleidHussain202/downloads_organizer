"""The scan pipeline: list -> filter -> classify -> move."""

from __future__ import annotations

from dataclasses import dataclass, field

from .mover import execute_move, plan_move
from .rules import classify, resolve_rules
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
    store=None,
    previous_sizes: dict | None = None,
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

    active_rules = resolve_rules(rules)

    for entry in entries:
        if not entry.is_file():
            continue
        report.scanned += 1
        if not is_stable(entry, quiet_seconds=quiet_seconds, previous_sizes=previous_sizes):
            if previous_sizes is not None:
                try:
                    previous_sizes[entry] = entry.stat().st_size
                except OSError:
                    pass
            continue
        category = classify(entry.name, active_rules)
        if category is None:
            continue
        try:
            size_before = entry.stat().st_size
        except OSError:
            size_before = 0
        plan = plan_move(entry, dest_root / category)
        if store is not None and not dry_run:
            store.write_intent(str(entry), str(plan.dst))
        result = execute_move(plan, dry_run=dry_run)
        if result.ok:
            if store is not None and not dry_run:
                store.clear_intent(str(result.dst))
                if str(result.dst) != str(plan.dst):
                    store.clear_intent(str(plan.dst))
            if store is not None:
                store.record_move(str(plan.src), str(result.dst), category, size_before, dry_run)
            if previous_sizes is not None:
                previous_sizes.pop(entry, None)
            report.moved.append(result)
        else:
            report.errors += 1
            report.notes.append(f"move failed: {result.error}")
    return report

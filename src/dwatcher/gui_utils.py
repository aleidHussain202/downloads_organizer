from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def format_size(n: int) -> str:
    n = int(n)
    if n < 1024:
        return f"{n} B"
    v = float(n)
    for unit in ("KB", "MB", "GB"):
        v /= 1024.0
        if v < 1024:
            return f"{v:.1f} {unit}"
    return f"{v:.1f} TB"


def open_folder(path: Path) -> None:
    target = str(Path(path).parent if Path(path).suffix else path)
    try:
        import os
        if hasattr(os, "startfile"):
            os.startfile(target)
            return
    except Exception:
        pass
    if sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])


def token_lines(state, db_path) -> list[str]:
    return [f"Watch:  {state.watch_dir}", f"Dest:   {state.dest_root}",
            f"Interval: {state.interval}s", f"Quiet:  {state.quiet_seconds}s",
            f"DryRun: {state.dry_run}", f"DB:     {db_path}"]


_STATUS_DOT_COLORS: dict[str, str] = {
    "Watching": "#3FB950",
    "Paused": "#D29922",
    "Error": "#F85149",
}


def status_dot(status: str) -> tuple[str, str]:
    """Status dot glyph + color (text label carries meaning; never color-only)."""
    return ("●", _STATUS_DOT_COLORS.get(status, "#9AA0A6"))


def summarize(moved: int, errors: int) -> str:
    """One-line session summary for the dashboard header."""
    return f"{moved} moved this session · {errors} errors"


def stripe(i: int) -> str:
    """Row-striping tag for the moves table: ``"even"`` or ``"odd"``."""
    return "even" if i % 2 == 0 else "odd"


_EVENT_KINDS = ("scan", "moved", "note", "error")


def format_event(kind: str, detail: str) -> tuple[str, str]:
    """Normalize an activity-feed entry to an ``(event, detail)`` pair."""
    if kind in _EVENT_KINDS:
        return (kind, detail)
    return ("note", detail)

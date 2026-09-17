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

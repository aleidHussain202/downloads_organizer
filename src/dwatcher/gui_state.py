from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GuiState:
    watch_dir: Path
    dest_root: Path
    rules: dict | None
    quiet_seconds: int
    interval: int
    dry_run: bool
    db_path: Path
    paused: bool = False
    running: bool = True

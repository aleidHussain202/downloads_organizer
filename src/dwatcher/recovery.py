"""Crash-safe recovery driven by the write-ahead intent journal."""
from __future__ import annotations
import os
import shutil
from pathlib import Path
from .mover import unique_destination


def _same_file(a: str, b: str) -> bool:
    try:
        sa, sb = os.stat(a), os.stat(b)
        return sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime)
    except OSError:
        return False


def recover_pending(store, dry_run: bool = False) -> list[str]:
    actions: list[str] = []
    for src, dst in store.pending_intents():
        try:
            src_exists = os.path.exists(src)
            dst_exists = os.path.exists(dst)
            if not src_exists and dst_exists:
                store.clear_intent(dst)
                actions.append(f"cleared: {dst} (move had completed)")
            elif src_exists and not dst_exists:
                if dry_run:
                    actions.append(f"would move: {src} -> {dst}")
                    continue
                os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                final = Path(unique_destination(Path(dst)))
                shutil.move(src, str(final))
                store.clear_intent(str(final))
                if str(final) != dst:
                    store.clear_intent(dst)
                actions.append(f"moved: {src} -> {final}")
            elif src_exists and dst_exists:
                if _same_file(src, dst):
                    try:
                        if not dry_run:
                            os.remove(src)
                            store.clear_intent(dst)
                            actions.append(f"removed duplicate src: {src}")
                        else:
                            actions.append(f"would remove duplicate src: {src} (dry run)")
                    except OSError as exc:
                        actions.append(f"could not remove {src}: {exc}")
                else:
                    if dry_run:
                        actions.append(f"would rename: {src} (dst differs)")
                        continue
                    final = Path(unique_destination(Path(dst)))
                    shutil.move(src, str(final))
                    store.clear_intent(str(final))
                    store.clear_intent(dst)
                    actions.append(f"moved colliding src: {src} -> {final}")
            else:
                store.clear_intent(dst)
                actions.append(f"missing both sides: {src} -> {dst} (cleared)")
        except Exception as exc:
            actions.append(f"could not recover {src} -> {dst}: {exc}")
            continue
    return actions

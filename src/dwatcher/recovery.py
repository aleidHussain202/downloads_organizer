"""Crash-safe recovery driven by the write-ahead intent journal."""

from __future__ import annotations

import shutil


def recover_pending(store) -> list[str]:
    """Resolve every pending intent. Returns human-readable actions.

    For each (src, dst) intent:
      - src missing, dst present  -> move happened, clear intent
      - src present, dst missing  -> move never ran, do it now
      - both present              -> dst exists; remove src copy, clear
      - both missing              -> report, clear
    """
    actions: list[str] = []
    for src, dst in store.pending_intents():
        src_exists = shutil.os.path.exists(src)
        dst_exists = shutil.os.path.exists(dst)
        if not src_exists and dst_exists:
            store.clear_intent(dst)
            actions.append(f"cleared: {dst} (move had completed)")
        elif src_exists and not dst_exists:
            parent = shutil.os.path.dirname(dst)
            shutil.os.makedirs(parent, exist_ok=True)
            final = _unique(dst)
            shutil.move(src, final)
            store.clear_intent(str(final))
            actions.append(f"moved: {src} -> {final}")
        elif src_exists and dst_exists:
            try:
                shutil.os.remove(src)
                actions.append(f"removed duplicate src: {src}")
            except OSError as exc:
                actions.append(f"could not remove {src}: {exc}")
            store.clear_intent(dst)
            actions.append(f"cleared: {dst}")
        else:
            store.clear_intent(dst)
            actions.append(f"missing both sides: {src} -> {dst} (cleared)")
    return actions


def _unique(dst):
    if not shutil.os.path.exists(dst):
        return dst
    stem, ext = shutil.os.path.splitext(dst)
    n = 1
    while shutil.os.path.exists(f"{stem} ({n}){ext}"):
        n += 1
    return f"{stem} ({n}){ext}"

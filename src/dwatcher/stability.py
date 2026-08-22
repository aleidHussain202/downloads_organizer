"""Deciding when a watched file is a *completed* download."""

from __future__ import annotations

import os
import time

# extensions/suffixes that mark in-flight downloads across common browsers
PARTIAL_SUFFIXES = (".crdownload", ".part", ".opdownload", ".tmp")


def is_partial(path) -> bool:
    """True if the file's name marks it as still downloading."""
    name = path.name.lower()
    if name.endswith(PARTIAL_SUFFIXES):
        return True
    return name.endswith(".download")  # Firefox: archive.zip.download


def is_stable(
    path,
    quiet_seconds: int = 30,
    previous_sizes: dict | None = None,
    now: float | None = None,
) -> bool:
    """A file is stable when it exists, isn't partial, its size hasn't
    changed since the previous scan, and its mtime is at least
    quiet_seconds old.
    """
    try:
        st = path.stat()
    except OSError:
        return False

    if is_partial(path):
        return False

    t = time.time() if now is None else now
    age = t - st.st_mtime
    if age < quiet_seconds:
        return False

    if previous_sizes and path in previous_sizes:
        if previous_sizes[path] != st.st_size:
            return False  # grew since last scan -> still downloading

    return True

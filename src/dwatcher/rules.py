"""Classification rules: map file extensions to destination categories."""

from __future__ import annotations

# extension (lowercase, with dot) -> category folder name
DEFAULT_RULES: dict[str, str] = {
    # Installers
    ".exe": "Installers",
    ".msi": "Installers",
    ".msix": "Installers",
    ".msp": "Installers",
    ".appx": "Installers",
    # Documents
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".xls": "Documents",
    ".xlsx": "Documents",
    ".ppt": "Documents",
    ".pptx": "Documents",
    ".txt": "Documents",
    ".md": "Documents",
    ".csv": "Documents",
    ".epub": "Documents",
    ".mobi": "Documents",
    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".webp": "Images",
    ".bmp": "Images",
    ".svg": "Images",
    ".ico": "Images",
    # Archives
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".bz2": "Archives",
    ".xz": "Archives",
    ".iso": "Archives",
    # Audio
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".ogg": "Audio",
    ".m4a": "Audio",
    # Video
    ".mp4": "Video",
    ".mkv": "Video",
    ".avi": "Video",
    ".mov": "Video",
    ".webm": "Video",
}


def normalize_ext(ext: str) -> str:
    e = ext.strip().lower()
    return e if e.startswith(".") else f".{e}"


def resolve_rules(custom: dict | None = None) -> dict:
    """Merge custom over DEFAULT_RULES. [] opts out. Validates types."""
    if custom is None:
        return dict(DEFAULT_RULES)
    merged: dict = dict(DEFAULT_RULES)
    for k, v in custom.items():
        if not isinstance(k, str):
            raise TypeError(f"rule key {k!r} must be str")
        if not (isinstance(v, str) or isinstance(v, list)):
            raise TypeError(f"rule {k!r} must be str or list, got {type(v).__name__}")
        if isinstance(v, list) and v != []:
            raise ValueError(f"rule {k!r} list must be [] (opt-out)")
        merged[normalize_ext(k)] = v
    return merged


def classify(filename: str, rules: dict[str, str | list] | None = None) -> str | None:
    """Return the destination category for *filename*.

    rules are merged over DEFAULT_RULES. A rule value of [] (empty list) means
    "never touch this extension". Returns None when no rule matches.
    """
    active = resolve_rules(rules)
    ext = ""
    dot = filename.rfind(".")
    if dot > 0:  # >0 so dotfiles like ".gitignore" have no extension
        ext = filename[dot:].lower()

    if not ext:
        return None

    if ext in active:
        target = active[ext]
        if isinstance(target, list):
            return None  # explicit opt-out
        return target
    return None

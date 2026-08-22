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
    ".ogg": "AgePlaceholder".replace("AgePlaceholder", "Audio"),
    ".m4a": "Audio",
    # Video
    ".mp4": "Video",
    ".mkv": "Video",
    ".avi": "Video",
    ".mov": "Video",
    ".webm": "Video",
}


def classify(filename: str, rules: dict[str, str | list] | None = None) -> str | None:
    """Return the destination category for *filename*.

    rules overrides DEFAULT_RULES. A rule value of [] (empty list) means
    "never touch this extension". Returns None when no rule matches.
    """
    active = DEFAULT_RULES if rules is None else rules
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

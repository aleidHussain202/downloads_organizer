"""Dark theme visual contract for the dwatcher tkinter GUI.

Stdlib-only ``ttk.Style`` theme. Owns the locked palette and the single
``apply_theme()`` entry point consumed by ``gui.py``. No ``tk.Tk()``
construction here by design (headless-safe; tests use a fake style).
"""

from __future__ import annotations

from typing import Any

PALETTE: dict[str, str] = {
    "BG": "#1B1E23",
    "SURFACE": "#242830",
    "BORDER": "#353B45",
    "TEXT": "#E8EAED",
    "MUTED": "#9AA0A6",
    "ACCENT": "#5B9DFF",
    "SUCCESS": "#3FB950",
    "WARNING": "#D29922",
    "DANGER": "#F85149",
    "ROW_ALT": "#20242B",
    "SELECT": "#26436B",
}

FONTS: dict[str, tuple[str, ...]] = {
    "UI": ("Segoe UI", "TkDefaultFont"),
    "MONO": ("Consolas", "TkFixedFont"),
}


def apply_theme(style: Any) -> None:
    """Apply the dark theme to a ``ttk.Style`` (or test double)."""
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure("TFrame", background=PALETTE["BG"])
    style.configure("TLabel", background=PALETTE["BG"],
                    foreground=PALETTE["TEXT"])
    style.configure("TButton", background=PALETTE["SURFACE"],
                    foreground=PALETTE["TEXT"],
                    bordercolor=PALETTE["BORDER"], padding=6)
    style.configure("TCheckbutton", background=PALETTE["BG"],
                    foreground=PALETTE["TEXT"])
    style.configure("TNotebook", background=PALETTE["BG"],
                    bordercolor=PALETTE["BORDER"])
    style.configure("TNotebook.Tab", background=PALETTE["SURFACE"],
                    foreground=PALETTE["TEXT"], padding=(8, 4))
    style.configure("TLabelframe", background=PALETTE["BG"],
                    foreground=PALETTE["TEXT"],
                    bordercolor=PALETTE["BORDER"])
    style.configure("Treeview", background=PALETTE["SURFACE"],
                    fieldbackground=PALETTE["SURFACE"],
                    foreground=PALETTE["TEXT"],
                    bordercolor=PALETTE["BORDER"], rowheight=26)
    style.configure("Treeview.Heading", background=PALETTE["BORDER"],
                    foreground=PALETTE["TEXT"])

    style.map("TButton",
              background=[("active", PALETTE["SELECT"]),
                          ("disabled", PALETTE["SURFACE"])],
              foreground=[("disabled", PALETTE["MUTED"])],
              bordercolor=[("active", PALETTE["ACCENT"])])
    style.map("TNotebook.Tab",
              background=[("selected", PALETTE["SELECT"])],
              foreground=[("selected", PALETTE["TEXT"])])
    style.map("Treeview",
              background=[("selected", PALETTE["SELECT"])],
              foreground=[("selected", PALETTE["TEXT"])])

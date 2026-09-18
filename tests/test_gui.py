def test_format_size_no_decimal_for_bytes():
    from dwatcher.gui_utils import format_size
    assert format_size(512) == "512 B"
    assert format_size(2048) == "2.0 KB"


def test_open_folder_falls_back(monkeypatch, tmp_path):
    import os
    from dwatcher import gui_utils
    monkeypatch.delattr(os, "startfile", raising=False)
    called = {}
    import subprocess
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: called.setdefault("ok", True))
    gui_utils.open_folder(tmp_path)  # must not raise
    assert called.get("ok") is True


def test_pause_toggle_without_tk():
    from dwatcher.gui_state import GuiState
    from pathlib import Path
    s = GuiState(Path("w"), Path("d"), None, 30, 10, False, Path("x.db"))
    s.paused = not s.paused
    assert s.paused is True


def test_token_lines_contains_dryrun():
    from dwatcher.gui_utils import token_lines
    from dwatcher.gui_state import GuiState
    from pathlib import Path
    s = GuiState(Path("w"), Path("d"), None, 30, 10, True, Path("x.db"))
    assert any("DryRun: True" in line for line in token_lines(s, Path("x.db")))


class FakeStyle:
    def __init__(self):
        self.used = None; self.configured = {}; self.mapped = {}
    def theme_use(self, name=None):
        if name is None: return "clam"
        self.used = name
    def configure(self, name, **kw): self.configured[name] = kw
    def map(self, name, **kw): self.mapped[name] = kw


def test_apply_theme_sets_dark_styles():
    from dwatcher.gui_theme import apply_theme, PALETTE
    st = FakeStyle()
    apply_theme(st)
    assert st.used == "clam"
    assert st.configured["TButton"]["padding"] == 6
    assert st.configured["Treeview"]["rowheight"] == 26
    assert st.configured["Treeview"]["background"] == PALETTE["SURFACE"]
    assert "TNotebook" in st.configured


def test_palette_contrast():
    from dwatcher.gui_theme import PALETTE
    def lum(h):
        c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
        c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    l1, l2 = lum(PALETTE["TEXT"]), lum(PALETTE["SURFACE"])
    assert (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05) >= 7.0


def test_status_dot_mapping():
    from dwatcher.gui_utils import status_dot
    assert status_dot("Watching") == ("●", "#3FB950")
    assert status_dot("Paused") == ("●", "#D29922")
    assert status_dot("Error") == ("●", "#F85149")
    assert status_dot("Anything-else") == ("●", "#9AA0A6")


def test_summarize():
    from dwatcher.gui_utils import summarize
    assert summarize(12, 0) == "12 moved this session · 0 errors"


def test_stripe_alternates_even_odd():
    from dwatcher.gui_utils import stripe
    assert stripe(0) == "even"
    assert stripe(1) == "odd"
    assert stripe(2) == "even"

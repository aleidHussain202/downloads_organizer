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

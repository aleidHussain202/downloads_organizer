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

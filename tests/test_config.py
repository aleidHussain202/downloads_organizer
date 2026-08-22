"""Tests for dwatcher.config — TOML config load with defaults."""
import pytest

from dwatcher.config import load_config


def write_cfg(tmp_path, text):
    p = tmp_path / "dwatcher.toml"
    p.write_text(text)
    return p


class TestLoadConfig:
    def test_defaults_when_file_missing(self, tmp_path):
        cfg = load_config(tmp_path / "nope.toml")
        assert cfg["quiet_seconds"] == 30
        assert cfg["interval"] == 10
        assert "watch_dir" in cfg and "dest_root" in cfg

    def test_overrides_from_toml(self, tmp_path):
        p = write_cfg(tmp_path, """
[watch]
dir = "C:/tmp/drop"
dest = "C:/tmp/sorted"
interval = 5
quiet_seconds = 60
dry_run = true
""")
        cfg = load_config(p)
        assert str(cfg["watch_dir"]).replace("\\", "/").endswith("tmp/drop")
        assert cfg["interval"] == 5
        assert cfg["quiet_seconds"] == 60
        assert cfg["dry_run"] is True

    def test_invalid_toml_raises_clear_error(self, tmp_path):
        p = write_cfg(tmp_path, "not [valid toml")
        with pytest.raises(ValueError, match="config"):
            load_config(p)

    def test_custom_rules_table(self, tmp_path):
        p = write_cfg(tmp_path, """
[watch]
dir = "C:/d"
[rules]
".stl" = "3DPrints"
""")
        cfg = load_config(p)
        assert cfg["rules"][".stl"] == "3DPrints"

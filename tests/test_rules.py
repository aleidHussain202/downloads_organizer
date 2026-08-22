"""Tests for dwatcher.rules — classify files into destination categories."""
import pytest

from dwatcher.rules import classify, DEFAULT_RULES


class TestClassify:
    def test_installer_exe_goes_to_installers(self):
        c = classify("SteamSetup.exe")
        assert c == "Installers"

    def test_pdf_goes_to_documents(self):
        assert classify("paper.pdf") == "Documents"

    def test_image_jpg_goes_to_images(self):
        assert classify("photo.jpg") == "Images"

    def test_zip_goes_to_archives(self):
        assert classify("backup.zip") == "Archives"

    def test_mp3_goes_to_audio(self):
        assert classify("song.mp3") == "Audio"

    def test_mp4_goes_to_video(self):
        assert classify("movie.mp4") == "Video"

    def test_unknown_extension_returns_none(self):
        # .xyz has no rule -> unclassified
        assert classify("mystery.xyz") is None

    def test_no_extension_returns_none(self):
        assert classify("README") is None

    def test_case_insensitive_extension(self):
        assert classify("Setup.EXE") == "Installers"

    def test_custom_rules_override_defaults(self):
        rules = {".stl": "3DPrints"}
        assert classify("part.stl", rules) == "3DPrints"

    def test_custom_rules_can_remove_default_category(self):
        # empty list for an extension means "do not touch"
        assert classify("notes.txt", {".txt": []}) is None


class TestDefaultRules:
    def test_every_category_has_at_least_one_extension(self):
        cats = set(DEFAULT_RULES.values())
        assert {"Installers", "Documents", "Images", "Archives", "Audio",
                "Video"} <= cats

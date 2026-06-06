"""Tests for interface/config.py — constants introduced in this PR."""

from pathlib import Path

from interface.config import BACKENDS, DEFAULT_FILE, DEFAULT_SERIES, IMAGE_EXTS, OUTPUT_DIR, ROOT_DIR


class TestConfigConstants:
    def test_backends_contains_all_six(self):
        assert set(BACKENDS) == {"python", "rust", "cpp", "java", "csharp", "js"}

    def test_backends_is_ordered_list(self):
        assert isinstance(BACKENDS, list)
        assert len(BACKENDS) == 6

    def test_image_exts_contains_common_formats(self):
        for ext in (".png", ".jpg", ".jpeg", ".pgm", ".ppm"):
            assert ext in IMAGE_EXTS

    def test_image_exts_lowercase(self):
        for ext in IMAGE_EXTS:
            assert ext == ext.lower()

    def test_root_dir_is_absolute(self):
        assert ROOT_DIR.is_absolute()

    def test_root_dir_exists(self):
        assert ROOT_DIR.exists()

    def test_default_file_is_under_root(self):
        assert str(DEFAULT_FILE).startswith(str(ROOT_DIR))

    def test_default_series_is_under_root(self):
        assert str(DEFAULT_SERIES).startswith(str(ROOT_DIR))

    def test_output_dir_is_under_root(self):
        assert str(OUTPUT_DIR).startswith(str(ROOT_DIR))

    def test_default_file_is_path_object(self):
        assert isinstance(DEFAULT_FILE, Path)

    def test_default_series_is_path_object(self):
        assert isinstance(DEFAULT_SERIES, Path)

    def test_output_dir_is_path_object(self):
        assert isinstance(OUTPUT_DIR, Path)

    def test_default_file_has_dcm_extension(self):
        assert DEFAULT_FILE.suffix == ".dcm"

    def test_image_exts_is_a_set(self):
        assert isinstance(IMAGE_EXTS, set)
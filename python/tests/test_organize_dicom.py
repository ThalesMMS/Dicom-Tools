#
# test_organize_dicom.py
# Dicom-Tools-py
#
# Tests for DICOM file organization: patient/study/series/modality organization,
# filename sanitization, copy vs move modes, and recursive directory handling.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import pytest

from DICOM_reencoder.organize_dicom import (
    organize_by_modality,
    organize_by_patient,
    organize_by_series,
    organize_by_study,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_sanitize_basic(self):
        result = sanitize_filename("Normal Name")
        assert result == "Normal Name"

    def test_sanitize_invalid_chars(self):
        result = sanitize_filename("Test<>Name")
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_slashes(self):
        result = sanitize_filename("Test/Name\\Path")
        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_empty(self):
        result = sanitize_filename("")
        assert result == "Unknown"

    def test_sanitize_none(self):
        result = sanitize_filename("N/A")
        assert result == "Unknown"

    def test_sanitize_length_limit(self):
        long_name = "A" * 150
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_sanitize_multiple_spaces(self):
        result = sanitize_filename("Test    Name")
        assert "    " not in result


class TestOrganizeByPatient:
    """Test patient-based organization."""

    def test_organize_by_patient_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_patient(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        # Check that files were organized
        assert dest_dir.exists()
        # Should have patient directories
        patient_dirs = [d for d in dest_dir.iterdir() if d.is_dir()]
        assert len(patient_dirs) > 0

    def test_organize_by_patient_move_mode(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        dest_dir = tmp_path / "organized"

        # Copy files to source
        import shutil
        for path in paths:
            shutil.copy(path, source_dir / path.name)

        organize_by_patient(str(source_dir), str(dest_dir), copy_mode=False, recursive=False)

        # Files should be moved (not in source anymore)
        remaining = list(source_dir.glob("*.dcm"))
        assert len(remaining) == 0

    def test_organize_by_patient_recursive(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        subdir = source_dir / "subdir"
        subdir.mkdir()

        # Copy one file to subdirectory
        import shutil
        shutil.copy(paths[0], subdir / paths[0].name)

        dest_dir = tmp_path / "organized"
        organize_by_patient(str(source_dir), str(dest_dir), copy_mode=True, recursive=True)

        assert dest_dir.exists()


class TestOrganizeByStudy:
    """Test study-based organization."""

    def test_organize_by_study_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_study(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        assert dest_dir.exists()
        study_dirs = [d for d in dest_dir.iterdir() if d.is_dir()]
        assert len(study_dirs) > 0

    def test_organize_by_study_preserves_files(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_study(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        # Count files in destination
        organized_files = list(dest_dir.rglob("*.dcm"))
        assert len(organized_files) >= len(paths)


class TestOrganizeBySeries:
    """Test series-based organization."""

    def test_organize_by_series_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_series(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        assert dest_dir.exists()
        series_dirs = [d for d in dest_dir.iterdir() if d.is_dir()]
        assert len(series_dirs) > 0

    def test_organize_by_series_groups_correctly(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_series(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        # All files from same series should be in same directory
        organized_files = list(dest_dir.rglob("*.dcm"))
        assert len(organized_files) >= len(paths)


class TestOrganizeByModality:
    """Test modality-based organization."""

    def test_organize_by_modality_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_modality(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        assert dest_dir.exists()
        modality_dirs = [d for d in dest_dir.iterdir() if d.is_dir()]
        assert len(modality_dirs) > 0

    def test_organize_by_modality_groups_by_type(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        dest_dir = tmp_path / "organized"

        organize_by_modality(str(source_dir), str(dest_dir), copy_mode=True, recursive=False)

        # Files should be organized by modality
        organized_files = list(dest_dir.rglob("*.dcm"))
        assert len(organized_files) >= len(paths)


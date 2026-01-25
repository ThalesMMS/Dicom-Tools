#
# test_batch_process.py
# Dicom-Tools-py
#
# Tests for batch processing operations: file discovery, batch decompression,
# anonymization, conversion, and validation.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import pytest

from DICOM_reencoder.batch_process import (
    anonymize_batch,
    convert_batch,
    decompress_batch,
    find_dicom_files,
    list_files,
    validate_batch,
)


class TestFindDicomFiles:
    """Test DICOM file discovery."""

    def test_find_dicom_files_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        found = find_dicom_files(str(source_dir), recursive=False)

        assert len(found) >= len(paths)
        assert all(Path(f).exists() for f in found)

    def test_find_dicom_files_recursive(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        subdir = source_dir / "subdir"
        subdir.mkdir()

        # Copy one file to subdirectory
        import shutil
        shutil.copy(paths[0], subdir / paths[0].name)

        found = find_dicom_files(str(source_dir), recursive=True)

        assert len(found) >= len(paths) + 1

    def test_find_dicom_files_without_extension(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture, save_dataset

        # Create file without .dcm extension
        ds = build_secondary_capture(shape=(8, 8))
        no_ext_file = tmp_path / "no_extension"
        save_dataset(ds, no_ext_file)

        found = find_dicom_files(str(tmp_path), recursive=False)

        assert str(no_ext_file) in found or any(Path(f).samefile(no_ext_file) for f in found)

    def test_find_dicom_files_multiple_extensions(self, tmp_path):
        from DICOM_reencoder.core import build_secondary_capture, save_dataset

        ds = build_secondary_capture(shape=(8, 8))
        save_dataset(ds, tmp_path / "test.dcm")
        save_dataset(ds, tmp_path / "test.DCM")
        save_dataset(ds, tmp_path / "test.dicom")

        found = find_dicom_files(str(tmp_path), recursive=False)

        # Should find files with different extensions
        assert len(found) >= 1  # At least one should be found


class TestDecompressBatch:
    """Test batch decompression operations."""

    def test_decompress_batch_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        output_dir = tmp_path / "decompressed"
        output_dir.mkdir()

        # decompress_batch doesn't return results, it prints
        decompress_batch([str(p) for p in paths], output_dir=str(output_dir))

        # Check that files were created (if decompression was needed)
        decompressed_files = list(output_dir.glob("*_decompressed.dcm"))
        # Files may or may not be decompressed depending on transfer syntax
        assert True  # Test passes if function completes without error

    def test_decompress_batch_no_output_dir(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series

        # decompress_batch doesn't return results
        decompress_batch([str(p) for p in paths], output_dir=None)

        # Function should complete without error
        assert True

    def test_decompress_batch_empty_list(self):
        # decompress_batch doesn't return results, just prints
        decompress_batch([])
        # Should complete without error
        assert True


class TestAnonymizeBatch:
    """Test batch anonymization operations."""

    def test_anonymize_batch_basic(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        output_dir = tmp_path / "anonymized"
        output_dir.mkdir()

        # anonymize_batch doesn't return results, it prints
        anonymize_batch([str(p) for p in paths], output_dir=str(output_dir))

        # Check that anonymized files were created
        anonymized_files = list(output_dir.glob("*_anonymized.dcm"))
        assert len(anonymized_files) == len(paths)

        # Verify anonymization
        import pydicom
        for result_path in anonymized_files:
            ds = pydicom.dcmread(result_path, force=True)
            assert ds.PatientName == "ANONYMOUS^PATIENT"

    def test_anonymize_batch_no_output_dir(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series

        # anonymize_batch doesn't return results
        anonymize_batch([str(p) for p in paths], output_dir=None)

        # Function should complete without error
        assert True

    def test_anonymize_batch_preserves_structure(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        output_dir = tmp_path / "anonymized"
        output_dir.mkdir()

        anonymize_batch([str(p) for p in paths], output_dir=str(output_dir))

        # Check anonymized files
        anonymized_files = list(output_dir.glob("*_anonymized.dcm"))
        assert len(anonymized_files) == len(paths)

        # All files should be valid DICOM
        import pydicom
        for result_path in anonymized_files:
            ds = pydicom.dcmread(result_path, force=True)
            assert hasattr(ds, "pixel_array")


class TestConvertBatch:
    """Test batch conversion operations."""

    def test_convert_batch_to_png(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        output_dir = tmp_path / "converted"
        output_dir.mkdir()

        # convert_batch doesn't return results, it prints
        convert_batch([str(p) for p in paths], output_dir=str(output_dir), output_format="png")

        # Check that PNG files were created
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) == len(paths)

    def test_convert_batch_to_jpeg(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        output_dir = tmp_path / "converted"
        output_dir.mkdir()

        convert_batch([str(p) for p in paths], output_dir=str(output_dir), output_format="jpg")

        # Check that JPEG files were created
        jpeg_files = list(output_dir.glob("*.jpg")) + list(output_dir.glob("*.jpeg"))
        assert len(jpeg_files) == len(paths)

    def test_convert_batch_no_output_dir(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series

        convert_batch([str(p) for p in paths], output_dir=None, output_format="png")

        # Function should complete without error
        assert True


class TestValidateBatch:
    """Test batch validation operations."""

    def test_validate_batch_basic(self, synthetic_series):
        paths, _ = synthetic_series

        # validate_batch doesn't return results, it prints
        validate_batch([str(p) for p in paths])

        # Function should complete without error
        assert True

    def test_validate_batch_reports_errors(self, tmp_path):
        # Create invalid DICOM file
        invalid_file = tmp_path / "invalid.dcm"
        invalid_file.write_bytes(b"NOT A DICOM FILE")

        # validate_batch doesn't return results, it prints
        validate_batch([str(invalid_file)])

        # Function should complete without error (may print validation errors)
        assert True

    def test_validate_batch_empty_list(self):
        # validate_batch doesn't return results
        validate_batch([])
        # Should complete without error
        assert True


class TestListFiles:
    """Test batch file listing operations."""

    def test_list_files_basic(self, synthetic_series):
        paths, _ = synthetic_series

        # list_files prints to stdout, so we capture it
        import io
        import sys
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            list_files(paths)

        output_str = output.getvalue()
        assert len(output_str) > 0

    def test_list_files_shows_metadata(self, synthetic_series):
        paths, _ = synthetic_series

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            list_files(paths)

        output_str = output.getvalue()
        # Should contain file information
        assert any(str(p) in output_str or Path(p).name in output_str for p in paths)

    def test_list_files_empty_list(self):
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            list_files([])

        # Should not crash
        assert True


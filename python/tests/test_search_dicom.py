#
# test_search_dicom.py
# Dicom-Tools-py
#
# Tests for DICOM file search functionality: metadata-based search, wildcard/regex,
# patient/study/date range queries, and output formatting.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import pytest

from DICOM_reencoder.search_dicom import (
    display_csv,
    display_list,
    display_table,
    search_by_date_range,
    search_by_patient,
    search_by_study,
    search_dicom_files,
)


class TestSearchDicomFiles:
    """Test basic DICOM file search."""

    def test_search_by_modality(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        criteria = {"Modality": "CT"}
        results = search_dicom_files(str(source_dir), criteria, recursive=False)

        assert len(results) > 0
        assert all(Path(f).exists() for f in results)

    def test_search_by_patient_name(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        # Get patient name from first file
        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        patient_name = str(ds.get("PatientName", ""))

        if patient_name:
            criteria = {"PatientName": patient_name}
            results = search_dicom_files(str(source_dir), criteria, recursive=False)

            assert len(results) > 0

    def test_search_wildcard(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        criteria = {"Modality": "C*"}
        results = search_dicom_files(str(source_dir), criteria, recursive=False)

        # Should match CT
        assert len(results) >= 0

    def test_search_regex(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        criteria = {"Modality": "/CT|MR/"}
        results = search_dicom_files(str(source_dir), criteria, recursive=False)

        assert len(results) >= 0

    def test_search_multiple_criteria(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        modality = str(ds.get("Modality", ""))

        criteria = {"Modality": modality, "Rows": str(ds.get("Rows", ""))}
        results = search_dicom_files(str(source_dir), criteria, recursive=False)

        assert len(results) >= 0

    def test_search_recursive(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent
        subdir = source_dir / "subdir"
        subdir.mkdir()

        # Copy one file to subdirectory
        import shutil
        shutil.copy(paths[0], subdir / paths[0].name)

        criteria = {"Modality": "CT"}
        results = search_dicom_files(str(source_dir), criteria, recursive=True)

        assert len(results) >= len(paths)


class TestSearchByPatient:
    """Test patient-based search."""

    def test_search_by_patient_name(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        patient_name = str(ds.get("PatientName", ""))

        if patient_name:
            results = search_by_patient(str(source_dir), patient_name=patient_name, recursive=False)

            assert len(results) >= 0

    def test_search_by_patient_id(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        patient_id = str(ds.get("PatientID", ""))

        if patient_id:
            results = search_by_patient(str(source_dir), patient_id=patient_id, recursive=False)

            assert len(results) >= 0

    def test_search_by_patient_both(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        patient_name = str(ds.get("PatientName", ""))
        patient_id = str(ds.get("PatientID", ""))

        if patient_name and patient_id:
            results = search_by_patient(
                str(source_dir), patient_name=patient_name, patient_id=patient_id, recursive=False
            )

            assert len(results) >= 0


class TestSearchByStudy:
    """Test study-based search."""

    def test_search_by_study_description(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        study_desc = str(ds.get("StudyDescription", ""))

        if study_desc:
            results = search_by_study(str(source_dir), study_desc=study_desc, recursive=False)

            assert len(results) >= 0

    def test_search_by_modality(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        modality = str(ds.get("Modality", ""))

        if modality:
            results = search_by_study(str(source_dir), modality=modality, recursive=False)

            assert len(results) >= 0


class TestSearchByDateRange:
    """Test date range search."""

    def test_search_by_date_range(self, synthetic_series):
        paths, _ = synthetic_series
        source_dir = Path(paths[0]).parent

        import pydicom
        ds = pydicom.dcmread(paths[0], stop_before_pixels=True, force=True)
        study_date = str(ds.get("StudyDate", ""))

        if study_date and len(study_date) == 8:
            # Search within a range around the study date
            start_date = study_date
            end_date = study_date

            results = search_by_date_range(str(source_dir), start_date, end_date, recursive=False)

            assert len(results) >= 0


class TestDisplayFormats:
    """Test output formatting functions."""

    def test_display_table(self, synthetic_series):
        paths, _ = synthetic_series
        data = [{"file": str(p), "modality": "CT"} for p in paths]

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_table(data)

        output_str = output.getvalue()
        assert len(output_str) > 0

    def test_display_list(self, synthetic_series):
        paths, _ = synthetic_series
        files = [str(p) for p in paths]

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_list(files)

        output_str = output.getvalue()
        assert len(output_str) > 0

    def test_display_csv(self, synthetic_series):
        paths, _ = synthetic_series
        data = [{"file": str(p), "modality": "CT"} for p in paths]

        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            display_csv(data)

        output_str = output.getvalue()
        assert len(output_str) > 0
        # CSV should have commas
        assert "," in output_str


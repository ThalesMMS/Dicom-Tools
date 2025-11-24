#
# metadata.py
# Dicom-Tools-py
#
# Extracts and summarizes DICOM metadata into lightweight dictionaries.
#
# Thales Matheus Mendonça Santos - November 2025

"""Metadata extraction helpers."""

from pydicom.dataset import Dataset


def _stringify(dataset: Dataset, key: str, default: str = "N/A") -> str:
    # Convert tag values to strings while tolerating missing attributes
    value = dataset.get(key, default)
    return str(value) if value is not None else default


def summarize_metadata(dataset: Dataset) -> dict:
    """Create a condensed metadata view used by the web API and tests."""
    return {
        "patient": {
            "name": _stringify(dataset, "PatientName"),
            "id": _stringify(dataset, "PatientID"),
            "birth_date": _stringify(dataset, "PatientBirthDate"),
            "sex": _stringify(dataset, "PatientSex"),
            "age": _stringify(dataset, "PatientAge"),
        },
        "study": {
            "description": _stringify(dataset, "StudyDescription"),
            "date": _stringify(dataset, "StudyDate"),
            "time": _stringify(dataset, "StudyTime"),
            "id": _stringify(dataset, "StudyID"),
            "instance_uid": _stringify(dataset, "StudyInstanceUID"),
        },
        "series": {
            "description": _stringify(dataset, "SeriesDescription"),
            "number": _stringify(dataset, "SeriesNumber"),
            "modality": _stringify(dataset, "Modality"),
            "instance_uid": _stringify(dataset, "SeriesInstanceUID"),
        },
        "image": {
            "instance_number": _stringify(dataset, "InstanceNumber"),
            "rows": _stringify(dataset, "Rows"),
            "columns": _stringify(dataset, "Columns"),
            "bits_allocated": _stringify(dataset, "BitsAllocated"),
            "photometric_interpretation": _stringify(dataset, "PhotometricInterpretation"),
            "window_center": _stringify(dataset, "WindowCenter"),
            "window_width": _stringify(dataset, "WindowWidth"),
        },
    }

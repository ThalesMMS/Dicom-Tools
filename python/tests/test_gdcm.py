#
# test_gdcm.py
# Dicom-Tools-py
#
# Checks that GDCM reads synthetic DICOM files and exposes pixel buffers correctly.
#
# Thales Matheus Mendonça Santos - November 2025

import pytest


gdcm = pytest.importorskip("gdcm")


def test_gdcm_reads_synthetic_dicom(synthetic_dicom_path):
    # GDCM should be able to parse and expose pixel buffers for generated fixtures
    reader = gdcm.ImageReader()
    reader.SetFileName(str(synthetic_dicom_path))
    assert reader.Read()

    image = reader.GetImage()
    dims = image.GetDimensions()
    assert dims[0] == 32
    assert dims[1] == 32
    assert image.GetBufferLength() > 0

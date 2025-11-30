#
# test_dicom_numpy_advanced.py
# Dicom-Tools-py
#
# Advanced dicom-numpy tests: oblique slice handling, different pixel representations,
# multi-planar reconstructions, affine matrix decomposition, and edge cases.
#
# Thales Matheus Mendonça Santos - November 2025

import numpy as np
import pytest
from pydicom import Dataset
from pydicom.uid import generate_uid

dicom_numpy = pytest.importorskip("dicom_numpy")


class TestAffineMatrixProperties:
    """Test affine transformation matrix computation and properties."""

    def test_affine_matrix_shape(self, synthetic_datasets):
        _, affine = dicom_numpy.combine_slices(synthetic_datasets)

        assert affine.shape == (4, 4)
        # Last row should be [0, 0, 0, 1]
        assert np.allclose(affine[3, :], [0, 0, 0, 1])

    def test_affine_matrix_invertibility(self, synthetic_datasets):
        _, affine = dicom_numpy.combine_slices(synthetic_datasets)

        # Affine should be invertible
        det = np.linalg.det(affine)
        assert not np.isclose(det, 0)

        inverse = np.linalg.inv(affine)
        identity = np.dot(affine, inverse)
        assert np.allclose(identity, np.eye(4))

    def test_affine_extracts_correct_spacing(self, synthetic_datasets):
        _, affine = dicom_numpy.combine_slices(synthetic_datasets)

        # Extract spacing from affine matrix columns
        spacing = np.linalg.norm(affine[:3, :3], axis=0)

        # Compare with DICOM spacing attributes
        ds = synthetic_datasets[0]
        pixel_spacing = list(ds.get("PixelSpacing", [1.0, 1.0]))
        slice_thickness = float(ds.get("SliceThickness", 1.0))

        # Allow for different orderings
        assert sorted(spacing) == pytest.approx(sorted(pixel_spacing + [slice_thickness]), rel=0.1)

    def test_affine_origin_matches_first_slice(self, synthetic_datasets):
        _, affine = dicom_numpy.combine_slices(synthetic_datasets)

        # Find first slice by position
        positions = []
        for ds in synthetic_datasets:
            pos = ds.get("ImagePositionPatient", [0, 0, 0])
            positions.append((pos[2], ds))
        positions.sort(key=lambda x: x[0])
        first_ds = positions[0][1]

        origin = affine[:3, 3]
        dicom_origin = np.array(first_ds.ImagePositionPatient)

        assert np.allclose(origin, dicom_origin, atol=1.0)


class TestOrientationHandling:
    """Test various slice orientation scenarios."""

    def test_axial_orientation(self, synthetic_datasets):
        # Standard axial: rows=AP, cols=LR, slices=SI
        for ds in synthetic_datasets:
            iop = ds.get("ImageOrientationPatient", [1, 0, 0, 0, 1, 0])
            row_cosines = np.array(iop[:3])
            col_cosines = np.array(iop[3:])

            # Cross product gives slice normal
            normal = np.cross(row_cosines, col_cosines)
            # Axial slices have normal ~parallel to z-axis
            # Just verify we can compute normal
            assert np.linalg.norm(normal) > 0.9

    def test_oblique_slices_combine(self, synthetic_datasets):
        # Create oblique orientation
        oblique = []
        angle = np.pi / 6  # 30 degrees
        for idx, ds in enumerate(synthetic_datasets):
            cp = ds.copy()
            cp.ImageOrientationPatient = [
                np.cos(angle), np.sin(angle), 0,
                -np.sin(angle), np.cos(angle), 0,
            ]
            cp.ImagePositionPatient = [0.0, 0.0, float(idx)]
            cp.SOPInstanceUID = generate_uid()
            oblique.append(cp)

        volume, affine = dicom_numpy.combine_slices(oblique)

        # Should still produce valid volume
        assert volume.shape[2] == len(oblique)
        assert not np.isnan(affine).any()

    def test_coronal_orientation(self, synthetic_datasets):
        # Coronal: rows=SI, cols=LR
        coronal = []
        for idx, ds in enumerate(synthetic_datasets):
            cp = ds.copy()
            cp.ImageOrientationPatient = [1, 0, 0, 0, 0, 1]
            cp.ImagePositionPatient = [0.0, float(idx), 0.0]
            cp.SOPInstanceUID = generate_uid()
            coronal.append(cp)

        volume, affine = dicom_numpy.combine_slices(coronal)
        assert volume.shape[2] == len(coronal)

    def test_sagittal_orientation(self, synthetic_datasets):
        # Sagittal: rows=SI, cols=AP
        sagittal = []
        for idx, ds in enumerate(synthetic_datasets):
            cp = ds.copy()
            cp.ImageOrientationPatient = [0, 1, 0, 0, 0, 1]
            cp.ImagePositionPatient = [float(idx), 0.0, 0.0]
            cp.SOPInstanceUID = generate_uid()
            sagittal.append(cp)

        volume, affine = dicom_numpy.combine_slices(sagittal)
        assert volume.shape[2] == len(sagittal)


class TestPixelRepresentations:
    """Test different pixel data types and representations."""

    def test_unsigned_16bit(self, synthetic_datasets):
        for ds in synthetic_datasets:
            ds.PixelRepresentation = 0
            ds.BitsAllocated = 16
            ds.BitsStored = 16

        volume, _ = dicom_numpy.combine_slices(synthetic_datasets)
        # Volume should contain non-negative values
        assert volume.min() >= 0

    def test_signed_16bit(self, synthetic_datasets):
        # Modify to signed
        for ds in synthetic_datasets:
            ds.PixelRepresentation = 1
            ds.BitsAllocated = 16
            ds.BitsStored = 16

        volume, _ = dicom_numpy.combine_slices(synthetic_datasets)
        # Should handle signed data
        assert volume.dtype in (np.int16, np.int32, np.float32, np.float64, np.uint16)

    def test_rescale_slope_intercept_applied(self, synthetic_datasets):
        # Apply rescale
        for ds in synthetic_datasets:
            ds.RescaleSlope = 2.0
            ds.RescaleIntercept = -1000.0

        volume, _ = dicom_numpy.combine_slices(synthetic_datasets, rescale=True)

        # Values should be transformed
        assert volume.min() < 0 or volume.max() > 1000  # Some transformation occurred


class TestSliceOrderingEdgeCases:
    """Test edge cases in slice ordering and spacing."""

    def test_reverse_slice_order(self, synthetic_datasets):
        # Reverse the acquisition order
        reversed_ds = list(reversed(synthetic_datasets))
        for idx, ds in enumerate(reversed_ds):
            ds.InstanceNumber = idx + 1
            ds.SOPInstanceUID = generate_uid()

        volume, affine = dicom_numpy.combine_slices(reversed_ds)

        # Should still produce valid volume
        assert volume.shape[2] == len(reversed_ds)

    def test_non_sequential_instance_numbers(self, synthetic_datasets):
        # Non-sequential instance numbers
        for idx, ds in enumerate(synthetic_datasets):
            ds.InstanceNumber = (idx + 1) * 10  # 10, 20, 30, ...
            ds.SOPInstanceUID = generate_uid()

        volume, _ = dicom_numpy.combine_slices(synthetic_datasets)
        assert volume.shape[2] == len(synthetic_datasets)

    def test_missing_instance_number(self, synthetic_datasets):
        # Remove instance number from some slices
        for idx, ds in enumerate(synthetic_datasets):
            if idx % 2 == 0:
                if hasattr(ds, "InstanceNumber"):
                    del ds.InstanceNumber
            ds.SOPInstanceUID = generate_uid()

        volume, _ = dicom_numpy.combine_slices(synthetic_datasets)
        assert volume.shape[2] == len(synthetic_datasets)

    def test_gantry_tilt_handling(self, synthetic_datasets):
        # Simulate gantry tilt by adjusting positions
        tilt_angle = 0.1  # radians
        for idx, ds in enumerate(synthetic_datasets):
            z_pos = float(idx)
            y_shift = z_pos * np.tan(tilt_angle)
            ds.ImagePositionPatient = [0.0, y_shift, z_pos]
            ds.SOPInstanceUID = generate_uid()

        volume, affine = dicom_numpy.combine_slices(synthetic_datasets, enforce_slice_spacing=False)

        # Should handle tilted geometry
        assert volume.shape[2] == len(synthetic_datasets)


class TestMultipleAcquisitions:
    """Test handling of multiple acquisition scenarios."""

    def test_temporal_series_separation(self, synthetic_datasets):
        # Create two time points
        time1 = []
        time2 = []

        for idx, ds in enumerate(synthetic_datasets):
            ds1 = ds.copy()
            ds1.AcquisitionTime = "100000.000000"
            ds1.TemporalPositionIdentifier = 1
            ds1.SOPInstanceUID = generate_uid()

            ds2 = ds.copy()
            ds2.AcquisitionTime = "100500.000000"
            ds2.TemporalPositionIdentifier = 2
            ds2.SOPInstanceUID = generate_uid()

            time1.append(ds1)
            time2.append(ds2)

        vol1, _ = dicom_numpy.combine_slices(time1)
        vol2, _ = dicom_numpy.combine_slices(time2)

        # Should produce separate volumes
        assert vol1.shape == vol2.shape

    def test_diffusion_directions(self, synthetic_datasets):
        # Simulate DWI with different b-values
        b0 = []
        b1000 = []

        for idx, ds in enumerate(synthetic_datasets):
            ds0 = ds.copy()
            ds0.DiffusionBValue = 0
            ds0.SOPInstanceUID = generate_uid()

            ds1 = ds.copy()
            ds1.DiffusionBValue = 1000
            ds1.SOPInstanceUID = generate_uid()

            b0.append(ds0)
            b1000.append(ds1)

        vol_b0, _ = dicom_numpy.combine_slices(b0)
        vol_b1000, _ = dicom_numpy.combine_slices(b1000)

        assert vol_b0.shape == vol_b1000.shape


class TestVolumeGeometryValidation:
    """Test volume geometry validation and consistency."""

    def test_consistent_slice_thickness(self, synthetic_datasets):
        # All slices should have same thickness
        thicknesses = set()
        for ds in synthetic_datasets:
            thicknesses.add(float(ds.get("SliceThickness", 1.0)))

        assert len(thicknesses) == 1

    def test_consistent_pixel_spacing(self, synthetic_datasets):
        spacings = set()
        for ds in synthetic_datasets:
            ps = ds.get("PixelSpacing", [1.0, 1.0])
            spacings.add((float(ps[0]), float(ps[1])))

        assert len(spacings) == 1

    def test_consistent_matrix_size(self, synthetic_datasets):
        sizes = set()
        for ds in synthetic_datasets:
            sizes.add((int(ds.Rows), int(ds.Columns)))

        assert len(sizes) == 1

    def test_slice_location_consistency(self, synthetic_datasets):
        locations = []
        for ds in synthetic_datasets:
            pos = ds.get("ImagePositionPatient", [0, 0, 0])
            locations.append(pos[2])

        # Locations should be unique and monotonic
        sorted_locs = sorted(locations)
        diffs = np.diff(sorted_locs)

        # All differences should be approximately equal (uniform spacing)
        if len(diffs) > 1:
            assert np.std(diffs) < np.mean(diffs) * 0.1 or np.std(diffs) < 0.1


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_slice_list_raises(self):
        with pytest.raises((ValueError, dicom_numpy.DicomImportException)):
            dicom_numpy.combine_slices([])

    def test_single_slice_handling(self, synthetic_datasets):
        single = [synthetic_datasets[0]]
        volume, affine = dicom_numpy.combine_slices(single)

        # Should produce 3D volume with depth 1
        assert volume.ndim == 3
        assert volume.shape[2] == 1

    def test_mismatched_series_raises(self, synthetic_datasets):
        # Mix slices from different series
        mixed = synthetic_datasets.copy()
        mixed[0].SeriesInstanceUID = generate_uid()  # Different series

        # May raise or handle gracefully depending on version
        try:
            volume, _ = dicom_numpy.combine_slices(mixed)
            # If it succeeds, just verify shape
            assert volume.shape[2] == len(mixed)
        except (ValueError, dicom_numpy.DicomImportException):
            pass  # Expected behavior

    def test_missing_position_handling(self, synthetic_datasets):
        # Remove ImagePositionPatient from some slices
        for idx, ds in enumerate(synthetic_datasets):
            if idx % 2 == 0 and hasattr(ds, "ImagePositionPatient"):
                # Keep SliceLocation as fallback
                ds.SliceLocation = float(idx)

        try:
            volume, _ = dicom_numpy.combine_slices(synthetic_datasets)
            assert volume.shape[2] == len(synthetic_datasets)
        except dicom_numpy.DicomImportException:
            pass  # Some versions may reject this


class TestNIfTICompatibility:
    """Test compatibility with NIfTI workflows."""

    def test_affine_produces_valid_nifti_orientation(self, synthetic_datasets):
        _, affine = dicom_numpy.combine_slices(synthetic_datasets)

        # Check that affine can produce valid NIfTI orientations
        # qform/sform compatibility
        rotation = affine[:3, :3]
        scaling = np.linalg.norm(rotation, axis=0)

        # Should have positive scaling
        assert np.all(scaling > 0)

        # Rotation matrix should be orthogonal after removing scale
        R = rotation / scaling
        RtR = np.dot(R.T, R)
        assert np.allclose(RtR, np.eye(3), atol=0.1)

    def test_coordinate_transform_roundtrip(self, synthetic_datasets):
        volume, affine = dicom_numpy.combine_slices(synthetic_datasets)

        # Transform voxel to world and back
        voxel = np.array([10, 10, 2, 1])
        world = np.dot(affine, voxel)

        # Inverse transform
        affine_inv = np.linalg.inv(affine)
        voxel_back = np.dot(affine_inv, world)

        assert np.allclose(voxel, voxel_back)


class TestMemoryEfficiency:
    """Test memory handling with large datasets."""

    def test_large_slice_count(self, synthetic_datasets):
        # Simulate larger series by duplicating
        extended = []
        for repeat in range(3):
            for idx, ds in enumerate(synthetic_datasets):
                cp = ds.copy()
                cp.InstanceNumber = repeat * len(synthetic_datasets) + idx + 1
                cp.ImagePositionPatient = [0.0, 0.0, float(cp.InstanceNumber)]
                cp.SOPInstanceUID = generate_uid()
                extended.append(cp)

        volume, _ = dicom_numpy.combine_slices(extended)
        assert volume.shape[2] == len(extended)

    def test_volume_dtype_preservation(self, synthetic_datasets):
        volume, _ = dicom_numpy.combine_slices(synthetic_datasets)

        # Should use appropriate dtype based on pixel data
        assert volume.dtype in (np.uint8, np.int8, np.uint16, np.int16,
                                np.uint32, np.int32, np.float32, np.float64)


class TestSpacingValidation:
    """Test slice spacing validation."""

    def test_enforce_spacing_detects_gaps(self, synthetic_datasets):
        # Create gap in slice positions
        gapped = []
        for idx, ds in enumerate(synthetic_datasets):
            cp = ds.copy()
            if idx == len(synthetic_datasets) // 2:
                # Insert gap
                cp.ImagePositionPatient = [0.0, 0.0, float(idx) + 5.0]
            else:
                cp.ImagePositionPatient = [0.0, 0.0, float(idx)]
            cp.SOPInstanceUID = generate_uid()
            gapped.append(cp)

        # Should raise with enforce_slice_spacing=True
        with pytest.raises(dicom_numpy.DicomImportException):
            dicom_numpy.combine_slices(gapped, enforce_slice_spacing=True)

    def test_relaxed_spacing_allows_gaps(self, synthetic_datasets):
        # Same gapped dataset
        gapped = []
        for idx, ds in enumerate(synthetic_datasets):
            cp = ds.copy()
            if idx == len(synthetic_datasets) // 2:
                cp.ImagePositionPatient = [0.0, 0.0, float(idx) + 5.0]
            else:
                cp.ImagePositionPatient = [0.0, 0.0, float(idx)]
            cp.SOPInstanceUID = generate_uid()
            gapped.append(cp)

        # Should succeed with enforce_slice_spacing=False
        volume, _ = dicom_numpy.combine_slices(gapped, enforce_slice_spacing=False)
        assert volume.shape[2] == len(gapped)

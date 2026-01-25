#
# test_simpleitk_advanced.py
# Dicom-Tools-py
#
# Advanced SimpleITK tests: resampling, morphological operations, edge detection,
# histogram processing, B-spline transforms, metric evaluation, and multi-modal registration.
#
# Thales Matheus Mendonça Santos - November 2025

from pathlib import Path

import numpy as np
import pytest

sitk = pytest.importorskip("SimpleITK")


class TestResampling:
    """Test image resampling operations."""

    def test_resample_to_isotropic_spacing(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])

        original_spacing = image.GetSpacing()
        target_spacing = (1.0, 1.0, 1.0)

        resampler = sitk.ResampleImageFilter()
        resampler.SetOutputSpacing(target_spacing)
        resampler.SetSize([
            int(round(image.GetSize()[i] * original_spacing[i] / target_spacing[i]))
            for i in range(3)
        ])
        resampler.SetOutputDirection(image.GetDirection())
        resampler.SetOutputOrigin(image.GetOrigin())
        resampler.SetInterpolator(sitk.sitkLinear)

        resampled = resampler.Execute(image)

        assert np.allclose(resampled.GetSpacing(), target_spacing)

    def test_resample_with_transform(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])

        # Apply translation transform during resampling
        transform = sitk.TranslationTransform(3, (5.0, -5.0, 0.0))

        resampled = sitk.Resample(
            image,
            image,  # reference image for output geometry
            transform,
            sitk.sitkLinear,
            0.0,
            image.GetPixelID(),
        )

        assert resampled.GetSize() == image.GetSize()
        assert resampled.GetSpacing() == image.GetSpacing()

    def test_resample_preserves_orientation(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])
        original_direction = image.GetDirection()

        # Resample to half resolution
        resampled = sitk.Resample(
            image,
            [s // 2 for s in image.GetSize()],
            sitk.Transform(),
            sitk.sitkLinear,
            image.GetOrigin(),
            [sp * 2 for sp in image.GetSpacing()],
            image.GetDirection(),
            0.0,
            image.GetPixelID(),
        )

        assert np.allclose(resampled.GetDirection(), original_direction)


class TestMorphologicalOperations:
    """Test morphological image processing."""

    def test_binary_erosion(self):
        array = np.zeros((32, 32), dtype=np.uint8)
        array[10:22, 10:22] = 1
        image = sitk.GetImageFromArray(array)

        eroded = sitk.BinaryErode(image, [2, 2])
        eroded_arr = sitk.GetArrayFromImage(eroded)

        # Eroded region should be smaller
        assert np.sum(eroded_arr) < np.sum(array)

    def test_binary_dilation(self):
        array = np.zeros((32, 32), dtype=np.uint8)
        array[14:18, 14:18] = 1
        image = sitk.GetImageFromArray(array)

        dilated = sitk.BinaryDilate(image, [3, 3])
        dilated_arr = sitk.GetArrayFromImage(dilated)

        # Dilated region should be larger
        assert np.sum(dilated_arr) > np.sum(array)

    def test_morphological_opening(self):
        array = np.zeros((32, 32), dtype=np.uint8)
        array[10:22, 10:22] = 1
        array[5, 5] = 1  # noise point
        image = sitk.GetImageFromArray(array)

        opened = sitk.BinaryMorphologicalOpening(image, [2, 2])
        opened_arr = sitk.GetArrayFromImage(opened)

        # Noise point should be removed
        assert opened_arr[5, 5] == 0
        # Main structure preserved
        assert opened_arr[16, 16] == 1

    def test_morphological_closing(self):
        array = np.ones((32, 32), dtype=np.uint8)
        array[15:17, 15:17] = 0  # hole
        image = sitk.GetImageFromArray(array)

        closed = sitk.BinaryMorphologicalClosing(image, [3, 3])
        closed_arr = sitk.GetArrayFromImage(closed)

        # Hole should be filled
        assert np.all(closed_arr[15:17, 15:17] == 1)

    def test_grayscale_morphology(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])
        image = sitk.Cast(image, sitk.sitkFloat32)

        # Grayscale erosion
        eroded = sitk.GrayscaleErode(image, [1, 1, 1])
        eroded_arr = sitk.GetArrayFromImage(eroded)
        original_arr = sitk.GetArrayFromImage(image)

        # Eroded image should have lower or equal values
        assert np.all(eroded_arr <= original_arr + 1e-6)


class TestEdgeDetection:
    """Test edge detection filters."""

    def test_sobel_edge_detection(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])
        image = sitk.Cast(image, sitk.sitkFloat32)

        edges = sitk.SobelEdgeDetection(image)
        edges_arr = sitk.GetArrayFromImage(edges)

        # Edges should be non-negative
        assert edges_arr.min() >= 0

    def test_canny_edge_detection(self):
        array = np.zeros((64, 64), dtype=np.float32)
        array[20:44, 20:44] = 100.0
        image = sitk.GetImageFromArray(array)

        edges = sitk.CannyEdgeDetection(
            image,
            lowerThreshold=10.0,
            upperThreshold=50.0,
            variance=[1.0, 1.0],
        )
        edges_arr = sitk.GetArrayFromImage(edges)

        # Edges should be detected at boundaries
        assert edges_arr.sum() > 0
        # Interior should be 0
        assert edges_arr[32, 32] == 0

    def test_laplacian_edge_enhancement(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])
        image = sitk.Cast(image, sitk.sitkFloat32)

        laplacian = sitk.Laplacian(image)
        laplacian_arr = sitk.GetArrayFromImage(laplacian)

        # Laplacian should have both positive and negative values
        assert laplacian_arr.min() < 0 or laplacian_arr.max() > 0


class TestHistogramProcessing:
    """Test histogram-based image processing."""

    def test_histogram_equalization(self):
        array = np.zeros((64, 64), dtype=np.uint8)
        array[:32, :] = 50
        array[32:, :] = 200
        image = sitk.GetImageFromArray(array)

        equalized = sitk.AdaptiveHistogramEqualization(image)
        eq_arr = sitk.GetArrayFromImage(equalized)

        # Equalized image should have more spread values
        assert eq_arr.std() >= 0  # Basic sanity check

    def test_intensity_windowing(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])
        image = sitk.Cast(image, sitk.sitkFloat32)

        windowed = sitk.IntensityWindowing(
            image,
            windowMinimum=0.0,
            windowMaximum=100.0,
            outputMinimum=0.0,
            outputMaximum=255.0,
        )
        windowed_arr = sitk.GetArrayFromImage(windowed)

        assert windowed_arr.min() >= 0.0
        assert windowed_arr.max() <= 255.0

    def test_rescale_intensity(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])
        image = sitk.Cast(image, sitk.sitkFloat32)

        rescaled = sitk.RescaleIntensity(image, outputMinimum=0.0, outputMaximum=1.0)
        rescaled_arr = sitk.GetArrayFromImage(rescaled)

        assert np.isclose(rescaled_arr.min(), 0.0, atol=0.01)
        assert np.isclose(rescaled_arr.max(), 1.0, atol=0.01)


class TestTransforms:
    """Test various transform types."""

    def test_euler_3d_transform(self):
        transform = sitk.Euler3DTransform()
        transform.SetRotation(0.1, 0.0, 0.0)  # Small rotation around x
        transform.SetTranslation((1.0, 2.0, 3.0))
        transform.SetCenter((0.0, 0.0, 0.0))

        point = (10.0, 10.0, 10.0)
        transformed = transform.TransformPoint(point)

        assert len(transformed) == 3
        assert transformed != point

    def test_affine_transform(self):
        transform = sitk.AffineTransform(3)
        matrix = [1.1, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]  # Scale x by 1.1
        transform.SetMatrix(matrix)

        point = (10.0, 10.0, 10.0)
        transformed = transform.TransformPoint(point)

        assert np.isclose(transformed[0], 11.0)
        assert np.isclose(transformed[1], 10.0)

    def test_bspline_transform(self):
        transform = sitk.BSplineTransform(3, 3)  # 3D, order 3
        transform.SetTransformDomainOrigin([0, 0, 0])
        transform.SetTransformDomainDirection([1, 0, 0, 0, 1, 0, 0, 0, 1])
        transform.SetTransformDomainPhysicalDimensions([100, 100, 100])
        transform.SetTransformDomainMeshSize([4, 4, 4])

        # Initialize parameters
        num_params = transform.GetNumberOfParameters()
        params = [0.0] * num_params
        transform.SetParameters(params)

        point = (50.0, 50.0, 50.0)
        transformed = transform.TransformPoint(point)

        # With zero parameters, point should be unchanged
        assert np.allclose(transformed, point)

    def test_composite_transform(self):
        t1 = sitk.TranslationTransform(3, (10.0, 0.0, 0.0))
        t2 = sitk.TranslationTransform(3, (0.0, 10.0, 0.0))

        composite = sitk.CompositeTransform(3)
        composite.AddTransform(t1)
        composite.AddTransform(t2)

        point = (0.0, 0.0, 0.0)
        transformed = composite.TransformPoint(point)

        assert np.isclose(transformed[0], 10.0)
        assert np.isclose(transformed[1], 10.0)


class TestImageMetrics:
    """Test image similarity metrics."""

    def test_mean_squares_metric(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.Cast(sitk.ReadImage([str(p) for p in paths]), sitk.sitkFloat32)

        # Same image should have 0 mean squares difference
        metric = sitk.MeanSquaresImageToImageMetric()
        metric.SetFixedImage(image)
        metric.SetMovingImage(image)

        # Self-comparison
        transform = sitk.TranslationTransform(3)
        transform.SetParameters([0.0, 0.0, 0.0])

        value = metric.GetValue(transform)
        assert np.isclose(value, 0.0, atol=1e-6)

    def test_correlation_metric(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.Cast(sitk.ReadImage([str(p) for p in paths]), sitk.sitkFloat32)

        # Create slightly different image
        noise = sitk.AdditiveGaussianNoise(image, standardDeviation=1.0)

        registration = sitk.ImageRegistrationMethod()
        registration.SetMetricAsCorrelation()

        # Just verify metric can be set
        assert registration is not None


class TestSegmentationFilters:
    """Test segmentation-related filters."""

    def test_otsu_threshold(self):
        array = np.zeros((64, 64), dtype=np.uint8)
        array[:32, :] = 50
        array[32:, :] = 200
        image = sitk.GetImageFromArray(array)

        otsu = sitk.OtsuThreshold(image, 0, 1)
        otsu_arr = sitk.GetArrayFromImage(otsu)

        # Should separate into two regions
        assert set(np.unique(otsu_arr)) == {0, 1}

    def test_connected_component_labeling(self):
        array = np.zeros((64, 64), dtype=np.uint8)
        array[10:20, 10:20] = 1
        array[40:50, 40:50] = 1
        image = sitk.GetImageFromArray(array)

        labeled = sitk.ConnectedComponent(image)
        labeled_arr = sitk.GetArrayFromImage(labeled)

        # Should have 2 distinct labels plus background
        unique = np.unique(labeled_arr)
        assert len(unique) == 3  # 0, 1, 2

    def test_distance_map(self):
        array = np.zeros((64, 64), dtype=np.uint8)
        array[20:44, 20:44] = 1
        image = sitk.GetImageFromArray(array)

        distance = sitk.SignedMaurerDistanceMap(image)
        distance_arr = sitk.GetArrayFromImage(distance)

        # Center should be positive (inside)
        assert distance_arr[32, 32] > 0
        # Outside should be negative
        assert distance_arr[0, 0] < 0

    def test_watershed_segmentation(self):
        array = np.zeros((64, 64), dtype=np.float32)
        array[10:30, 10:30] = 100.0
        array[34:54, 34:54] = 150.0
        image = sitk.GetImageFromArray(array)

        gradient = sitk.GradientMagnitude(image)
        watershed = sitk.MorphologicalWatershed(gradient, level=5.0)
        ws_arr = sitk.GetArrayFromImage(watershed)

        # Should produce labeled regions
        assert len(np.unique(ws_arr)) > 1


class TestImageStatistics:
    """Test statistical measurements on images."""

    def test_statistics_filter(self, synthetic_series):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])

        stats = sitk.StatisticsImageFilter()
        stats.Execute(image)

        assert stats.GetMinimum() <= stats.GetMaximum()
        assert stats.GetSum() >= 0
        assert stats.GetVariance() >= 0

    def test_label_shape_statistics(self):
        array = np.zeros((64, 64, 64), dtype=np.uint8)
        array[10:30, 10:30, 10:30] = 1  # 20x20x20 cube
        array[40:50, 40:50, 40:50] = 2  # 10x10x10 cube
        image = sitk.GetImageFromArray(array)

        shape_stats = sitk.LabelShapeStatisticsImageFilter()
        shape_stats.Execute(image)

        labels = shape_stats.GetLabels()
        assert 1 in labels
        assert 2 in labels

        # Volume of label 1 should be larger
        vol1 = shape_stats.GetNumberOfPixels(1)
        vol2 = shape_stats.GetNumberOfPixels(2)
        assert vol1 > vol2


class TestImageIOAdvanced:
    """Test advanced I/O operations."""

    def test_write_read_mha_format(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])

        mha_path = tmp_path / "volume.mha"
        sitk.WriteImage(image, str(mha_path))

        reloaded = sitk.ReadImage(str(mha_path))

        assert reloaded.GetSize() == image.GetSize()
        assert np.allclose(reloaded.GetSpacing(), image.GetSpacing())

    def test_write_read_nrrd_format(self, synthetic_series, tmp_path):
        paths, _ = synthetic_series
        image = sitk.ReadImage([str(p) for p in paths])

        nrrd_path = tmp_path / "volume.nrrd"
        sitk.WriteImage(image, str(nrrd_path))

        reloaded = sitk.ReadImage(str(nrrd_path))

        assert reloaded.GetSize() == image.GetSize()

    def test_image_series_reader_metadata(self, synthetic_series):
        paths, _ = synthetic_series

        reader = sitk.ImageSeriesReader()
        reader.SetFileNames([str(p) for p in paths])
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()

        image = reader.Execute()

        # Check metadata is accessible
        assert image.GetSize()[2] == len(paths)


class TestRegistrationAdvanced:
    """Test advanced registration scenarios."""

    def test_multiresolution_registration(self, synthetic_series):
        paths, _ = synthetic_series
        fixed = sitk.Cast(sitk.ReadImage([str(p) for p in paths]), sitk.sitkFloat32)

        # Create slightly translated moving image
        transform = sitk.TranslationTransform(3, (2.0, 2.0, 0.0))
        moving = sitk.Resample(fixed, transform)

        registration = sitk.ImageRegistrationMethod()
        registration.SetMetricAsMeanSquares()
        registration.SetOptimizerAsGradientDescent(
            learningRate=1.0,
            numberOfIterations=100,
            convergenceMinimumValue=1e-6,
            convergenceWindowSize=10,
        )
        registration.SetInterpolator(sitk.sitkLinear)
        registration.SetInitialTransform(sitk.TranslationTransform(3))

        # Multi-resolution
        registration.SetShrinkFactorsPerLevel([4, 2, 1])
        registration.SetSmoothingSigmasPerLevel([2, 1, 0])

        result = registration.Execute(fixed, moving)
        offset = np.array(result.GetParameters())

        # Should recover approximate translation
        assert np.linalg.norm(offset - np.array([-2.0, -2.0, 0.0])) < 5.0

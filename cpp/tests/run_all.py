#
# run_all.py
# DicomToolsCpp
#
# Runs the compiled CLI against each module’s test command and checks for expected output artifacts.
#
# Thales Matheus Mendonça Santos - November 2025

import subprocess
import os
import sys
import shutil

# Configuration
BUILD_DIR = "build"
EXECUTABLE = os.path.join(BUILD_DIR, "DicomTools")
INPUT_FILE = os.path.join("..", "sample_series", "IM-0001-0001.dcm")
OUTPUT_DIR = "output"

# Ensure we fail early if the binary has not been built
if not os.path.exists(EXECUTABLE):
    print(f"Error: Executable not found at {EXECUTABLE}")
    sys.exit(1)

if not os.path.exists(INPUT_FILE):
    print(f"Error: Sample DICOM not found at {INPUT_FILE}")
    sys.exit(1)

# Reset output directory for a clean run
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_test(command, description):
    print(f"Testing: {description}...")
    cmd = [EXECUTABLE, command, "-i", INPUT_FILE, "-o", OUTPUT_DIR]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [FAILED] Return code: {result.returncode}")
        print(result.stderr)
        return False
    else:
        print(f"  [PASS]")
        return True

# Check outputs
def check_file(filename):
    # Simple existence check; contents are validated manually when needed
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        print(f"  [OK] Output file generated: {filepath}")
        return True
    else:
        print(f"  [FAIL] Missing output file: {filepath}")
        return False

# Track missing artifacts as test failures so the harness catches regressions
def require_file(filename):
    ok = check_file(filename)
    global tests_passed
    if not ok:
        tests_passed = False
    return ok

# Main
tests_passed = True

print("========================================")
print("      Automated Test Suite              ")
print("========================================")

# GDCM
if run_test("test-gdcm", "GDCM Features"):
    require_file("gdcm_anon.dcm")
    require_file("gdcm_raw.dcm")
    require_file("gdcm_reuid.dcm")
    require_file("gdcm_dump.txt")
    require_file("gdcm_jpeg2000.dcm")
    require_file("gdcm_rle.dcm")
    require_file("gdcm_jpegls.dcm")
    require_file("gdcm_stats.txt")
    require_file("gdcm_series_index.csv")
    require_file("gdcm_preview.pgm")
else:
    tests_passed = False

# DCMTK
if run_test("test-dcmtk", "DCMTK Features"):
    require_file("dcmtk_modified.dcm")
    require_file("dcmtk_pixel_output.ppm")
    require_file("dcmtk_jpeg_lossless.dcm")
    require_file("dcmtk_jpeg_baseline.dcm")
    require_file("dcmtk_rle.dcm")
    require_file("dcmtk_raw_dump.bin")
    require_file("dcmtk_explicit_vr.dcm")
    require_file("dcmtk_metadata.txt")
    require_file("validate.txt")
    require_file("dcmtk_preview.bmp")
    require_file("dcmtk_segmentation.dcm")
    require_file("dicomdir_media/DICOMDIR")
    require_file("dcmtk_sr.dcm")
    require_file("dcmtk_sr_summary.txt")
    require_file("dcmtk_rtstruct.txt")
    require_file("dcmtk_functional_groups.txt")
    require_file("dcmtk_waveform.txt")
else:
    tests_passed = False

# ITK
if run_test("test-itk", "ITK Features"):
    require_file("itk_canny.dcm")
    require_file("itk_gaussian.dcm")
    require_file("itk_median.dcm")
    require_file("itk_threshold.dcm")
    require_file("itk_otsu.dcm")
    require_file("itk_resampled.dcm")
    require_file("itk_aniso.dcm")
    require_file("itk_histogram_eq.dcm")
    require_file("itk_slice.png")
    require_file("itk_mip.png")
    require_file("itk_volume.nrrd")
    require_file("itk_volume.nii.gz")
    require_file("itk_connected_threshold.dcm")
    require_file("itk_distance_map.nrrd")
    require_file("itk_label_stats.txt")
    require_file("itk_registered.nrrd")
    require_file("itk_registration.txt")
    require_file("itk_vector.nrrd")
    require_file("itk_series.txt")
else:
    tests_passed = False

# VTK
if run_test("test-vtk", "VTK Features"):
    require_file("vtk_export.vti")
    require_file("vtk_resampled.vti")
    require_file("vtk_volume.nii.gz")
    require_file("vtk_isosurface.stl")
    require_file("vtk_mpr_slice.png")
    require_file("vtk_mip.png")
    require_file("vtk_threshold_mask.vti")
    require_file("vtk_connectivity_mask.vti")
    require_file("vtk_viewer_slice.png")
    require_file("vtk_metadata.txt")
    require_file("vtk_stats.txt")
    require_file("vtk_volume_render.png")
    require_file("vtk_fusion.png")
    require_file("vtk_time_series.txt")
    require_file("vtk_mpr_sagittal.png")
    require_file("vtk_overlay.png")
    require_file("vtk_labelmap.vti")
    require_file("vtk_label_surface.stl")
    require_file("vtk_labelmap_stats.txt")
    require_file("vtk_streaming.txt")
else:
    tests_passed = False

print("========================================")
if tests_passed:
    print("ALL TESTS PASSED")
    sys.exit(0)
else:
    print("SOME TESTS FAILED")
    sys.exit(1)

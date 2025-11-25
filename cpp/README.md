# Dicom-Tools-cpp

A modular C++ repository designed to demonstrate, test, and benchmark functionalities of major medical imaging libraries:
- **GDCM** (Grassroots DICOM)
- **DCMTK** (DICOM Toolkit)
- **ITK** (Insight Segmentation and Registration Toolkit)
- **VTK** (Visualization Toolkit)

## Quickstart

```bash
# Optional: build bundled dependencies locally (GDCM, DCMTK, ITK, VTK)
./scripts/build_deps.sh

# Configure and build
cmake -S . -B build
cmake --build build

# Inspect available modules/commands
./build/DicomTools --modules
./build/DicomTools --list

# Run everything on the sample DICOM
./build/DicomTools all -i sample_series/IM-0001-0001.dcm -o output
```

## Features Implemented

| Library | Feature | Description |
| :--- | :--- | :--- |
| **GDCM** | **Anonymization** | Redacts Patient Name, ID, and Birth Date. |
| | **Decompression** | Transcodes compressed DICOMs to Raw (Implicit VR Little Endian). |
| | **Tag Inspection** | Reads and displays common tags. |
| | **UID Rewrite** | Regenerates Study/Series/SOP Instance UIDs. |
| | **Dataset Dump** | Writes a verbose text dump of the DICOM dataset. |
| | **JPEG2000 Transcode** | Tests JPEG2000 lossless codec support. |
| | **RLE Transcode** | Validates encapsulated RLE Lossless support. |
| | **JPEG-LS Transcode** | Validates JPEG-LS Lossless transfer syntax support. |
| | **Pixel Stats** | Computes min/max/mean pixel statistics to text. |
| | **Directory Scan** | Recursively indexes series/tags into a CSV for QA. |
| | **Preview Export** | Writes an 8-bit PGM preview of the first slice. |
| | **Sequence Editing** | Creates/updates nested ReferencedSeriesSequence items. |
| | **DICOMDIR Read** | Summarizes patients/series from a DICOMDIR. |
| | **StringFilter Charset** | Exercises PN/LO decoding under non-default SpecificCharacterSet. |
| | **RT/SEG Read** | Summarizes ROI names and contour frames from RTSTRUCT/SEG. |
| **DCMTK** | **Tag Modification** | Modifies metadata (e.g., PatientID) and saves new files. |
| | **Pixel Extraction** | Extracts pixel data and exports as PGM/PPM images. |
| | **JPEG Lossless** | Re-encodes to JPEG Lossless (Process 14 SV1). |
| | **JPEG Baseline** | Re-encodes to JPEG Process 1 (lossy) to validate codecs. |
| | **RLE Transcode** | Re-encodes to RLE Lossless for decoder coverage. |
| | **Raw Dump** | Writes raw pixel buffer for regression checks. |
| | **Explicit VR Rewrite** | Transcodes to Explicit VR Little Endian. |
| | **Metadata Report** | Exports common patient/study attributes to text. |
| | **BMP Preview** | Generates an 8-bit BMP frame for quick visualization. |
| | **DICOMDIR Build** | Creates a lightweight DICOMDIR for the current series. |
| | **C-ECHO / C-STORE Loopback** | Spins up in-process SCP and validates round-trip store. |
| | **Charset Round-trip** | Writes UTF-8 PN/LO and validates reload consistency. |
| | **Secondary Capture** | Builds a brand-new SC instance with synthetic pixels. |
| | **Structured Report** | Generates a small SR (NUM + TEXT) and validates it. |
| | **RTSTRUCT Read** | Summarizes ROIs/contours from RTSTRUCT. |
| | **Functional Groups** | Dumps per-frame functional group info and frame preview. |
| **ITK** | **Edge Detection** | Applies Canny Edge Detection filter. |
| | **Smoothing** | Reduces noise using Discrete Gaussian Smoothing. |
| | **Median Filter** | Removes salt-and-pepper noise with a 3D median. |
| | **Segmentation** | Segments structures using Binary Thresholding or Otsu. |
| | **Anisotropic Denoise** | Curvature anisotropic diffusion smoothing. |
| | **Resampling** | Resamples volumes to isotropic spacing (1x1x1mm). |
| | **Histogram EQ** | Adaptive histogram equalization for contrast. |
| | **Slice Export** | Extracts the middle slice to PNG. |
| | **MIP** | Axial maximum intensity projection to PNG. |
| | **NRRD Export** | Writes the processed volume to `.nrrd` for interchange. |
| | **NIfTI Export** | Writes the volume to `.nii.gz` for interoperability. |
| | **Distance Map + Morphology** | Signed distance map + simple closing with summary stats. |
| | **Label Statistics** | Connected components with per-label min/max/mean/sigma. |
| | **Registration** | Estimates translation via MI and resamples moving image. |
| | **Vector Volume** | Composes multi-component volume and exports as NRRD. |
| | **DICOM Series Write** | Emits a fresh DICOM series with new UIDs. |
| **VTK** | **3D Mesh Generation** | Generates STL surfaces using Marching Cubes. |
| | **MPR** | Extracts 2D slices (Multi-Planar Reformatting) from 3D volumes. |
| | **Multiplanar MPR** | Sagittal, coronal, and oblique slice exports. |
| | **Isotropic Resample** | Resamples volume to 1mm spacing and saves VTI. |
| | **Volume Export** | Converts DICOM series to VTK XML Image Data (`.vti`). |
| | **NIfTI Export** | Writes the volume to `.nii.gz` for interoperability. |
| | **Threshold Mask** | Builds a binary mask volume from a HU window. |
| | **MIP** | Axial maximum intensity projection to PNG. |
| | **Metadata Export** | Writes patient/study metadata to text. |
| | **Volume Stats** | Computes min/max/mean/stddev for QA regression. |
| | **Volume Rendering** | Headless volume rendering snapshot via SmartVolumeMapper. |
| | **Mask Overlay** | Threshold-derived mask overlaid on axial slice. |
| | **Labelmap → Surface** | Threshold to labelmap, emit voxel stats, and export STL surface. |
| | **Streaming Reslice** | Processes volume in Z-chunks using update extents to mimic streaming. |

## Prerequisites

- **CMake** (3.15 or higher)
- **C++ Compiler** (C++17 support required)
- **Python 3** (for automated testing)

### Dependency Management

You can install the required libraries via your package manager (e.g., `brew install gdcm dcmtk itk vtk`). 

Alternatively, this repo includes a script to download and build all dependencies locally:

```bash
./scripts/build_deps.sh
```
*This will install dependencies into `deps/install`, which the CMake configuration automatically detects.*

## Building

1.  Create a build directory:
    ```bash
    mkdir build
    cd build
    ```

2.  Configure with CMake:
    ```bash
    cmake ..
    ```

3.  Build the project:
    ```bash
    cmake --build .
    ```

## Usage

The project generates a single executable `DicomTools` in the `build` directory. It supports subcommands to target specific libraries.

**Syntax:**
```bash
./build/DicomTools <command> [options]
```

**Useful options:**
- `-i, --input <path>`: DICOM file or series directory (defaults to first `.dcm` under `input/`).
- `-o, --output <dir>`: Output directory (defaults to `output/`).
- `-l, --list`: Show all registered commands.
- `-m, --modules`: Show module availability and feature coverage.
- `-h, --help`: CLI help.

**Explore quickly:**
- List everything: `./build/DicomTools --list`
- Check which libraries were compiled: `./build/DicomTools --modules`
- Run all suites: `./build/DicomTools all -i input/dcm_series/IM-0001-0190.dcm -o output`
- Run one suite: `./build/DicomTools test-gdcm -i ... -o ...`
- Run one feature: e.g., `./build/DicomTools dcmtk:metadata -i ... -o ...`

**High-level commands:**
- `test-gdcm`, `test-dcmtk`, `test-itk`, `test-vtk`: Run all feature tests in each module.
- `all`: Run every available test (shortcut to the above).

**Granular commands (examples):**
- `gdcm:anonymize`, `gdcm:dump`, `gdcm:transcode-j2k`, `gdcm:transcode-j2k-lossy`, `gdcm:transcode-rle`, `gdcm:transcode-rle-planar`, `gdcm:jpegls`, `gdcm:scan`, `gdcm:preview`, `gdcm:stats`
- `gdcm:sequence`, `gdcm:dicomdir`, `gdcm:charset`, `gdcm:rt`
- `dcmtk:jpeg-lossless`, `dcmtk:jpeg-baseline`, `dcmtk:rle`, `dcmtk:raw-dump`, `dcmtk:bmp`, `dcmtk:dicomdir`, `dcmtk:metadata`, `dcmtk:sr`, `dcmtk:rt`, `dcmtk:fg`
- `dcmtk:net`, `dcmtk:charset`, `dcmtk:secondary`
- `itk:gaussian`, `itk:median`, `itk:threshold`, `itk:otsu`, `itk:aniso`, `itk:histogram`, `itk:slice`, `itk:mip`, `itk:nrrd`, `itk:nifti`, `itk:resample`
- `itk:distance-map`, `itk:label-stats`, `itk:register`, `itk:vector`, `itk:dicom-series`
- `vtk:mask`, `vtk:metadata`, `vtk:isosurface`, `vtk:nifti`, `vtk:resample`, `vtk:mip`, `vtk:stats`
- `vtk:volume-render`, `vtk:mpr-multi`, `vtk:overlay`, `vtk:label-surface`, `vtk:stream`

Note: `dcmtk:dicomdir` copies the source series into `output/dicomdir_media/` and emits the DICOMDIR there so relative references remain valid.

**Examples:**
```bash
./build/DicomTools --list
./build/DicomTools test-itk --input sample_series/IM-0001-0001.dcm --output tmp/itk_out
./build/DicomTools vtk:mask
```

## Automated Testing

A Python script is provided to run the full suite of tests and verify that the expected output files are generated correctly in the `output/` directory.

```bash
python3 tests/run_all.py
```

## Interactive Interface (CLI/GUI)

Use the helper script to trigger any library suite or individual command without typing the full binaries:

```bash
# CLI menu (default paths: build/DicomTools, input/dcm_series/IM-0001-0190.dcm, output/)
python3 scripts/test_interface.py

# GUI with Tkinter (falls back to CLI if Tkinter is missing)
python3 scripts/test_interface.py --gui
```

## Outputs

- Artifacts are written to `output/` by default (override with `-o`).
- Suites emit multiple files (DICOM copies, PNG/PGM/BMP previews, CSV indexes, STL meshes, text reports). See `tests/run_all.py` for the expected filenames per suite.

## Project Structure

- `src/modules/`: Modular implementation for each library (GDCM, DCMTK, ITK, VTK).
- `input/`: Directory for test DICOM images.
- `output/`: All generated files (images, meshes, anonymized DICOMs) are saved here.
- `scripts/`: Helper scripts for dependency setup.

# C++ Unit Tests for DICOM Libraries

This directory contains standalone C++ unit tests for GDCM, DCMTK, ITK, and VTK libraries.

## Test Files

| File | Description |
|------|-------------|
| `test_framework.h` | Lightweight test framework with colored output and assertions |
| `test_gdcm.cpp` | GDCM library tests: file I/O, tags, codecs, anonymization, scanning |
| `test_dcmtk.cpp` | DCMTK library tests: datasets, codecs, image processing, validation |
| `test_itk.cpp` | ITK library tests: filtering, resampling, segmentation, statistics |
| `test_vtk.cpp` | VTK library tests: imaging, surface extraction, rendering primitives |

## Building

The tests are built automatically when `BUILD_TESTING` is enabled in CMake:

```bash
cd cpp
mkdir build && cd build
cmake .. -DBUILD_TESTING=ON
make
```

## Running Tests

### Individual test executables

```bash
./test_gdcm
./test_dcmtk
./test_itk
./test_vtk
```

### Via CTest

```bash
ctest --output-on-failure
```

### All C++ tests at once

```bash
make run_cpp_tests
```

## Test Coverage

### GDCM Tests
- Global dictionary availability
- Tag construction and VR types
- UID generation
- File reading and writing
- Transfer syntax handling
- Image buffer extraction
- JPEG, JPEG2000, RLE codec availability
- Anonymization primitives
- Directory and series scanning

### DCMTK Tests
- Data dictionary lookup
- Dataset creation and manipulation
- Sequence handling
- File I/O with transfer syntax
- DicomImage loading and pixel access
- JPEG codec registration
- Transfer syntax validation
- Memory stream operations

### ITK Tests
- Image creation with spacing/origin/direction
- DICOM series reading via GDCM IO
- Metadata extraction
- Gaussian, median, and threshold filters
- Otsu automatic thresholding
- Resampling with interpolation
- Statistics and min/max calculation
- Connected components
- Slice extraction

### VTK Tests
- ImageData creation and pixel access
- DICOM directory reading
- Image processing (cast, threshold, smooth, median)
- Resampling and reslicing
- Marching cubes surface extraction
- Statistics and histogram
- Color mapping with lookup tables
- Transform and matrix operations
- VTI and STL file writing
- Rendering pipeline setup

## Conditional Compilation

Tests are conditionally compiled based on library availability:
- `USE_GDCM` - Defined when GDCM is found
- `USE_DCMTK` - Defined when DCMTK is found
- `USE_ITK` - Defined when ITK is found
- `USE_VTK` - Defined when VTK is found

When a library is not available, the corresponding test file compiles but skips all library-specific tests with an informational message.

## Test Data

Tests automatically search for DICOM test files in these locations:
- `../sample_series`
- `../../sample_series`
- `../../../sample_series`
- `sample_series`

The `sample_series/` directory in the repository root contains sample DICOM files for testing.

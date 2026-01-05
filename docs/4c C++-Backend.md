# C++ Backend

> **Relevant source files**
> * [BUILD.md](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md)
> * [README.md](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md)
> * [interface/adapters/cpp_cli.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py)
> * [interface/app.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py)
> * [scripts/setup_all.sh](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/scripts/setup_all.sh)

## Purpose and Scope

This page documents the C++ backend implementation of the Dicom-Tools toolkit. The C++ backend leverages four major medical imaging libraries (DCMTK, GDCM, ITK, VTK) to provide DICOM file processing, advanced visualization, and specialized medical format support. It is particularly distinguished by its VTK-based 3D visualization capabilities and support for Structured Reports (SR) and Radiotherapy (RT) data structures.

For information about building all backends including C++, see [Build System](#8.1). For details on the CLI contract that the C++ backend implements, see [CLI Contract System](#3). For operation-specific documentation, see [DICOM Operations](#5).

---

## Architecture Overview

The C++ backend is built as a single executable (`DicomTools`) that provides multiple subcommands for different libraries and operations. Unlike the Python backend which uses separate commands, the C++ implementation uses a namespace-prefixed command structure (e.g., `gdcm:dump`, `vtk:export`).

```mermaid
flowchart TD

DicomTools["DicomTools (cpp/build/DicomTools)"]
GDCM["GDCM Module gdcm:*"]
DCMTK["DCMTK Module dcmtk:*"]
ITK["ITK Module itk:*"]
VTK["VTK Module vtk:*"]
GDCMOps["gdcm:dump gdcm:anonymize gdcm:preview gdcm:stats gdcm:transcode-*"]
DCMTKOps["dcmtk:dump dcmtk:anonymize dcmtk:parse"]
ITKOps["itk:stats itk:preview itk:validate"]
VTKBasic["vtk:export vtk:nifti vtk:metadata vtk:stats"]
VTKAdvanced["vtk:isosurface vtk:resample vtk:mip vtk:volume-render"]
VTKInteractive["vtk:viewer vtk:mpr-multi vtk:overlay vtk:stream"]
UnitTests["test_gdcm test_dcmtk test_itk test_vtk"]
IntegrationTests["test_integration test_edge_cases test_validation test_utils"]
TestRunner["run_cpp_tests"]

DicomTools -.-> GDCM
DicomTools -.-> DCMTK
DicomTools -.-> ITK
DicomTools -.-> VTK
GDCM -.-> GDCMOps
DCMTK -.-> DCMTKOps
ITK -.-> ITKOps
VTK -.-> VTKBasic
VTK -.-> VTKAdvanced
VTK -.-> VTKInteractive
DicomTools -.-> UnitTests
DicomTools -.-> IntegrationTests
DicomTools -.-> TestRunner

subgraph subGraph4 ["Test Suite"]
    UnitTests
    IntegrationTests
    TestRunner
end

subgraph subGraph3 ["VTK Visualization"]
    VTKBasic
    VTKAdvanced
    VTKInteractive
end

subgraph subGraph2 ["Core Operations"]
    GDCMOps
    DCMTKOps
    ITKOps
end

subgraph subGraph1 ["Library Modules"]
    GDCM
    DCMTK
    ITK
    VTK
end

subgraph subGraph0 ["C++ Backend Executable"]
    DicomTools
end
```

**Sources:** [interface/app.py L162-L179](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L162-L179)

 [interface/adapters/cpp_cli.py L55-L144](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L55-L144)

---

## Library Roles and Capabilities

The C++ backend integrates four major medical imaging libraries, each with distinct responsibilities:

| Library | Primary Use Cases | Operations Supported |
| --- | --- | --- |
| **GDCM** | DICOM parsing, transcoding, anonymization | `info`, `anonymize`, `to_image`, `transcode`, `validate`, `stats`, `dump` |
| **DCMTK** | Alternative DICOM parsing, network operations | `info`, `anonymize`, `to_image`, `transcode`, `validate`, `dump` |
| **ITK** | Image processing, format conversion | `to_image`, `validate`, `stats` |
| **VTK** | 3D visualization, volume rendering, MPR | All `vtk:*` operations (15+ visualization commands) |

```mermaid
flowchart TD

InputDCM["DICOM Input"]
GDCMReader["gdcm::ImageReader"]
GDCMAnon["gdcm::Anonymizer"]
GDCMWriter["gdcm::ImageWriter"]
GDCMTranscode["gdcm::ImageChangeTransferSyntax"]
DCMTKLoad["DcmFileFormat"]
DCMTKDataset["DcmDataset"]
DCMTKModify["DcmItem modifications"]
ITKReader["itk::ImageSeriesReader"]
ITKFilter["itk::ImageFilter"]
ITKWriter["itk::ImageFileWriter"]
VTKReader["vtkDICOMImageReader"]
VTKVolume["vtkImageData"]
VTKRender["vtkRenderer vtkVolumeMapper"]
VTKExport["vtkNIFTIImageWriter vtkMetaImageWriter"]

InputDCM -.-> GDCMReader
InputDCM -.-> DCMTKLoad
InputDCM -.-> ITKReader
InputDCM -.-> VTKReader

subgraph subGraph4 ["VTK Pipeline"]
    VTKReader
    VTKVolume
    VTKRender
    VTKExport
    VTKReader -.-> VTKVolume
    VTKVolume -.-> VTKRender
    VTKVolume -.-> VTKExport
end

subgraph subGraph3 ["ITK Pipeline"]
    ITKReader
    ITKFilter
    ITKWriter
    ITKReader -.-> ITKFilter
    ITKFilter -.-> ITKWriter
end

subgraph subGraph2 ["DCMTK Pipeline"]
    DCMTKLoad
    DCMTKDataset
    DCMTKModify
    DCMTKLoad -.-> DCMTKDataset
    DCMTKDataset -.-> DCMTKModify
end

subgraph subGraph1 ["GDCM Pipeline"]
    GDCMReader
    GDCMAnon
    GDCMWriter
    GDCMTranscode
    GDCMReader -.-> GDCMAnon
    GDCMReader -.-> GDCMTranscode
    GDCMAnon -.-> GDCMWriter
    GDCMTranscode -.-> GDCMWriter
end

subgraph subGraph0 ["DICOM File"]
    InputDCM
end
```

**Sources:** [interface/app.py L162-L179](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L162-L179)

 [README.md L8-L13](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L8-L13)

---

## Build System

The C++ backend uses CMake as its build system with a minimum version requirement of 3.15 and C++17 compiler support.

### Build Configuration

The build process is centralized through CMake configuration:

**Build Location:** `cpp/build/DicomTools`
**Environment Variable:** `CPP_DICOM_TOOLS_BIN` (override for custom binary location)

```mermaid
flowchart TD

CMakeLists["CMakeLists.txt"]
Configure["cmake -S . -B build"]
Build["cmake --build build"]
Binary["build/DicomTools"]
DCMTK_LIB["DCMTK"]
GDCM_LIB["GDCM"]
ITK_LIB["ITK"]
VTK_LIB["VTK"]
BuildDeps["scripts/build_deps.sh"]
SetupAll["scripts/setup_all.sh"]

BuildDeps -.->|"builds locally"| DCMTK_LIB
BuildDeps -.->|"builds locally"| GDCM_LIB
BuildDeps -.->|"builds locally"| ITK_LIB
BuildDeps -.->|"builds locally"| VTK_LIB
SetupAll -.->|"link"| Configure
SetupAll -.->|"automates"| Build

subgraph subGraph2 ["Optional Scripts"]
    BuildDeps
    SetupAll
end

subgraph Dependencies ["Dependencies"]
    DCMTK_LIB
    GDCM_LIB
    ITK_LIB
    VTK_LIB
end

subgraph subGraph0 ["Build Process"]
    CMakeLists
    Configure
    Build
    Binary
    CMakeLists -.->|"automates"| Configure
    Configure -.->|"link"| Build
    Build -.->|"link"| Binary
end
```

### Build Commands

Standard build sequence:

```
mkdir -p cpp/buildcd cpp/buildcmake -DCMAKE_BUILD_TYPE=Release ..cmake --build .
```

Using the unified setup script:

```
./scripts/setup_all.sh  # Builds C++ along with other backends
```

The build type can be controlled via the `BUILD_TYPE` environment variable (default: `Release`).

**Sources:** [scripts/setup_all.sh L29-L38](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/scripts/setup_all.sh#L29-L38)

 [README.md L18](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L18-L18)

 [BUILD.md L16-L17](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L16-L17)

---

## CLI Structure and Adapter Integration

The C++ backend is invoked through the `CppCliAdapter` class, which translates generic contract requests into backend-specific command invocations.

```mermaid
sequenceDiagram
  participant p1 as TkApp / contract_runner
  participant p2 as CppCliAdapter
  participant p3 as DicomTools executable
  participant p4 as File System

  p1->>p2: "handle(request)"
  note over p2: "request = {op, input, output, options}"
  p2->>p2: "_build_cmd(op | input | output | options)"
  alt Core DICOM Operation
    p2->>p2: "Map to gdcm:* or dcmtk:* command"
  else VTK Operation
    p2->>p2: "Map to vtk:* command"
  else Test Operation
    p2->>p2: "Map to test executable"
  end
  p2->>p2: "ensure_dir(output_dir)"
  p2->>p3: "subprocess.run([binary | subcommand | args])"
  p3->>p4: "Read DICOM input"
  p4-->>p3: "DICOM data"
  p3->>p3: "Process with library (GDCM/ITK/VTK)"
  p3->>p4: "Write output files"
  p3-->>p2: "stdout, stderr, returncode"
  p2->>p2: "parse_json_maybe(stdout)"
  p2-->>p1: "RunResult{ok, returncode, output_files, metadata}"
```

### Command Building Logic

The adapter implements operation-to-command mapping in `_build_cmd()`:

**Core Operations (GDCM-based):**

* `info` / `dump` → `gdcm:dump -i <input> -o <output_dir>`
* `anonymize` → `gdcm:anonymize -i <input> -o <output_dir>`
* `to_image` → `gdcm:preview -i <input> -o <output_dir>`
* `stats` → `gdcm:stats -i <input> -o <output_dir>`
* `transcode` → `gdcm:transcode-j2k` or `gdcm:transcode-rle` or `gdcm:jpegls` (based on `syntax` option)

**VTK Operations:**

* `vtk_export` → `vtk:export -i <series_dir> -o <output_dir>`
* `vtk_nifti` → `vtk:nifti -i <series_dir> -o <output_dir>`
* `vtk_volume_render` → `vtk:volume-render -i <series_dir> -o <output_dir>`
* And 12 more VTK visualization commands

**Test Executables:**

* `test_gdcm` → Execute `cpp/build/test_gdcm`
* `test_dcmtk` → Execute `cpp/build/test_dcmtk`
* `run_cpp_tests` → `cmake --build . --target run_cpp_tests`

**Sources:** [interface/adapters/cpp_cli.py L55-L144](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L55-L144)

---

## Output Directory Behavior

Unlike other backends that allow flexible output file paths, the C++ backend uses a directory-based output model:

```mermaid
flowchart TD

InputFile["DICOM File or Series Directory"]
ParseRequest["Parse request"]
DetermineOutDir["output_dir = Path(output) or cpp/output"]
EnsureDir["ensure_dir(output_dir)"]
BuildCmd["Build command with -o output_dir"]
ProcessOp["Execute operation"]
WriteFiles["Write output files to output_dir"]
GDCMOut["dump.txt pixel_stats.txt preview.pgm (original_name).dcm"]
VTKOut["volume.vti volume.nii.gz isosurface.vtp screenshot.png"]

InputFile -.-> ParseRequest
BuildCmd -.-> ProcessOp
WriteFiles -.-> GDCMOut
WriteFiles -.-> VTKOut

subgraph subGraph3 ["Output Files"]
    GDCMOut
    VTKOut
end

subgraph subGraph2 ["DicomTools Execution"]
    ProcessOp
    WriteFiles
    ProcessOp -.-> WriteFiles
end

subgraph subGraph1 ["CppCliAdapter Logic"]
    ParseRequest
    DetermineOutDir
    EnsureDir
    BuildCmd
    ParseRequest -.-> DetermineOutDir
    DetermineOutDir -.-> EnsureDir
    EnsureDir -.-> BuildCmd
end

subgraph Input ["Input"]
    InputFile
end
```

**Key Differences from Other Backends:**

| Backend | Output Style | Example |
| --- | --- | --- |
| Python | File path | `--output /path/to/output.dcm` |
| Rust | File path | `-o /path/to/output.png` |
| C++ | **Directory** | `-o /path/to/output_dir/` |

The adapter handles this automatically by:

1. Accepting output path from the request
2. Treating it as a directory (creating if needed)
3. Predicting output file names based on operation type
4. Returning these paths in `RunResult.output_files`

**Sources:** [interface/adapters/cpp_cli.py L55-L92](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L55-L92)

 [interface/app.py L728-L735](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L728-L735)

---

## VTK Visualization Capabilities

The C++ backend's most distinctive feature is its comprehensive VTK-based visualization toolkit, supporting 15+ specialized operations unavailable in other language backends.

### VTK Operations Catalog

| Category | Operations | Output Artifacts |
| --- | --- | --- |
| **Export & Conversion** | `vtk_export`, `vtk_nifti` | `.vti`, `.nii.gz`, `.mha`, `.nrrd` |
| **Volume Processing** | `vtk_resample`, `vtk_mask`, `vtk_connectivity` | Processed volume files |
| **Projections** | `vtk_mip` (Maximum Intensity Projection) | MIP images, MinIP, AIP |
| **3D Reconstruction** | `vtk_isosurface` | `.vtp` surface meshes |
| **Visualization** | `vtk_viewer`, `vtk_volume_render`, `vtk_mpr_multi` | Interactive windows, screenshots |
| **Analysis** | `vtk_metadata`, `vtk_stats` | Text reports with volume info |
| **Advanced** | `vtk_overlay`, `vtk_stream` | Multi-dataset visualization |

```mermaid
flowchart TD

SeriesDir["Series Directory (multiple .dcm files)"]
Reader["vtkDICOMImageReader Load all slices"]
ImageData["vtkImageData 3D volume"]
Resample["vtkImageResample vtk_resample"]
Mask["vtkImageMask vtk_mask"]
Connect["vtkImageConnectivity vtk_connectivity"]
MIP["vtkImageMaximumProjection vtk_mip"]
Iso["vtkMarchingCubes vtk_isosurface"]
VolumeRender["vtkVolumeRayCastMapper vtk_volume_render"]
MPR["vtkImageSliceMapper vtk_mpr_multi"]
Viewer["vtkRenderer vtk_viewer"]
NIfTI["vtkNIFTIImageWriter vtk_nifti"]
VTI["vtkXMLImageDataWriter vtk_export"]
Meta["vtkMetaImageWriter vtk_export"]
VolumeFiles["volume.vti volume.nii.gz volume.mha"]
SurfaceFiles["isosurface.vtp"]
Images["screenshot.png mip_axial.png"]
Reports["metadata.txt volume_stats.txt"]

SeriesDir -.-> Reader
Resample -.-> VolumeFiles
NIfTI -.-> VolumeFiles
VTI -.-> VolumeFiles
Meta -.-> VolumeFiles
Iso -.-> SurfaceFiles
VolumeRender -.-> Images
MPR -.-> Images
MIP -.-> Images
Connect -.-> Reports
Mask -.-> Reports

subgraph subGraph5 ["Output Artifacts"]
    VolumeFiles
    SurfaceFiles
    Images
    Reports
end

subgraph subGraph4 ["VTK Processing Pipeline"]
    Reader
    ImageData
    Reader -.-> ImageData
    ImageData -.-> Resample
    ImageData -.-> Mask
    ImageData -.-> Connect
    ImageData -.-> MIP
    ImageData -.-> Iso
    ImageData -.-> VolumeRender
    ImageData -.-> MPR
    ImageData -.-> Viewer
    ImageData -.-> NIfTI
    ImageData -.-> VTI
    ImageData -.-> Meta

subgraph subGraph3 ["Export Options"]
    NIfTI
    VTI
    Meta
end

subgraph subGraph2 ["Rendering Options"]
    VolumeRender
    MPR
    Viewer
end

subgraph subGraph1 ["Processing Options"]
    Resample
    Mask
    Connect
    MIP
    Iso
end
end

subgraph subGraph0 ["DICOM Series Input"]
    SeriesDir
end
```

### VTK Command Mapping

The adapter maps VTK operations to CLI subcommands:

```
vtk_map = {    "vtk_export": "vtk:export",    "vtk_nifti": "vtk:nifti",    "vtk_isosurface": "vtk:isosurface",    "vtk_resample": "vtk:resample",    "vtk_mask": "vtk:mask",    "vtk_connectivity": "vtk:connectivity",    "vtk_mip": "vtk:mip",    "vtk_metadata": "vtk:metadata",    "vtk_stats": "vtk:stats",    "vtk_viewer": "vtk:viewer",    "vtk_volume_render": "vtk:volume-render",    "vtk_mpr_multi": "vtk:mpr-multi",    "vtk_overlay": "vtk:overlay",    "vtk_stream": "vtk:stream",}
```

All VTK operations:

* Require a series directory as input (not a single file)
* Output to a directory (not a single file)
* Return the output directory path in `RunResult.output_files`

**Sources:** [interface/adapters/cpp_cli.py L95-L114](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L95-L114)

 [interface/app.py L131-L147](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L131-L147)

 [interface/app.py L769-L776](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L769-L776)

---

## Testing Infrastructure

The C++ backend includes a comprehensive test suite covering unit tests, integration tests, and edge case validation.

### Test Organization

```mermaid
flowchart TD

TestGDCM["test_gdcm (cpp/build/test_gdcm)"]
TestDCMTK["test_dcmtk (cpp/build/test_dcmtk)"]
TestITK["test_itk (cpp/build/test_itk)"]
TestVTK["test_vtk (cpp/build/test_vtk)"]
TestUtils["test_utils (cpp/build/test_utils)"]
TestIntegration["test_integration (cpp/build/test_integration)"]
TestEdgeCases["test_edge_cases (cpp/build/test_edge_cases)"]
TestValidation["test_validation (cpp/build/test_validation)"]
PythonRunner["python3 cpp/tests/run_all.py"]
CMakeRunner["cmake --build . --target run_cpp_tests"]
CTest["ctest"]
Unit["Unit Tests Individual library functionality"]
Integration["Integration Tests GDCM/DCMTK workflows"]
Edge["Edge Cases Error handling"]
Validation["Validation DICOM conformance"]

PythonRunner -.-> TestGDCM
PythonRunner -.-> TestDCMTK
PythonRunner -.-> TestITK
PythonRunner -.-> TestVTK
CMakeRunner -.-> TestGDCM
CMakeRunner -.-> TestDCMTK
CMakeRunner -.-> TestIntegration
CMakeRunner -.-> TestEdgeCases
CTest -.-> TestGDCM
CTest -.-> TestDCMTK
CTest -.-> TestITK
CTest -.-> TestVTK
CTest -.-> TestUtils
TestGDCM -.-> Unit
TestDCMTK -.-> Unit
TestITK -.-> Unit
TestVTK -.-> Unit
TestUtils -.-> Unit
TestIntegration -.-> Integration
TestEdgeCases -.-> Edge
TestValidation -.-> Validation

subgraph subGraph2 ["Test Categories"]
    Unit
    Integration
    Edge
    Validation
end

subgraph subGraph1 ["Test Runners"]
    PythonRunner
    CMakeRunner
    CTest
end

subgraph subGraph0 ["Test Executables"]
    TestGDCM
    TestDCMTK
    TestITK
    TestVTK
    TestUtils
    TestIntegration
    TestEdgeCases
    TestValidation
end
```

### Test Operations in the Contract

The adapter exposes test operations through the CLI contract, allowing them to be invoked via the TkApp GUI or contract runner:

| Operation | Executable | Working Directory | Description |
| --- | --- | --- | --- |
| `test_gdcm` | `cpp/build/test_gdcm` | `cpp/build` | GDCM unit tests |
| `test_dcmtk` | `cpp/build/test_dcmtk` | `cpp/build` | DCMTK unit tests |
| `test_itk` | `cpp/build/test_itk` | `cpp/build` | ITK unit tests |
| `test_vtk_unit` | `cpp/build/test_vtk` | `cpp/build` | VTK unit tests |
| `test_utils` | `cpp/build/test_utils` | `cpp/build` | Utility function tests |
| `test_integration` | `cpp/build/test_integration` | `cpp/build` | Integration tests |
| `test_edge_cases` | `cpp/build/test_edge_cases` | `cpp/build` | Edge case tests |
| `test_validation` | `cpp/build/test_validation` | `cpp/build` | Validation tests |
| `run_cpp_tests` | `cmake --build . --target run_cpp_tests` | `cpp/build` | Run all tests |

The adapter sets the working directory to `cpp/build` for all test operations to ensure they can find linked libraries and test data.

**Sources:** [interface/adapters/cpp_cli.py L33-L44](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L33-L44)

 [interface/adapters/cpp_cli.py L126-L143](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L126-L143)

 [interface/app.py L168-L178](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L168-L178)

### Running Tests

Three methods to execute the test suite:

**1. Python Test Runner:**

```
python3 cpp/tests/run_all.py
```

**2. CMake Target:**

```
cd cpp/buildcmake --build . --target run_cpp_tests
```

**3. CTest:**

```
cd cpp/buildctest
```

**Sources:** [README.md L18](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L18-L18)

 [BUILD.md L27](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L27-L27)

---

## Operation Reference

### Core DICOM Operations

| Operation | Command | Input | Output | Description |
| --- | --- | --- | --- | --- |
| `info` | `gdcm:dump` | DICOM file | `dump.txt` | Metadata extraction |
| `dump` | `gdcm:dump` | DICOM file | `dump.txt` | Complete dataset dump |
| `anonymize` | `gdcm:anonymize` | DICOM file | `(original_name).dcm` | PHI removal |
| `to_image` | `gdcm:preview` | DICOM file | `preview.pgm` | Frame extraction |
| `stats` | `gdcm:stats` | DICOM file | `pixel_stats.txt` | Pixel statistics |
| `transcode` | `gdcm:transcode-*` | DICOM file | `(original_name).dcm` | Transfer syntax conversion |
| `validate` | `gdcm:dump` | DICOM file | `dump.txt` | DICOM validation (proxy) |

### Transcode Syntax Options

The `transcode` operation supports multiple transfer syntaxes via the `syntax` option:

* `j2k`, `jpeg2000`, `jpeg2000-lossless`, `jpeg2000_lossless` → `gdcm:transcode-j2k`
* `rle`, `rle-lossless`, `rle_lossless` → `gdcm:transcode-rle`
* Other values (fallback) → `gdcm:jpegls`

**Sources:** [interface/adapters/cpp_cli.py L61-L92](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L61-L92)

 [interface/app.py L362-L394](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L362-L394)

---

## Environment Configuration

The C++ backend supports runtime configuration through environment variables:

| Variable | Purpose | Default Value |
| --- | --- | --- |
| `CPP_DICOM_TOOLS_BIN` | Override path to DicomTools executable | `cpp/build/DicomTools` |
| `BUILD_TYPE` | CMake build configuration (during build) | `Release` |

### Binary Path Resolution

The adapter resolves the binary path with the following logic:

```
default_bin = os.environ.get("CPP_DICOM_TOOLS_BIN",                              str(root / "cpp" / "build" / "DicomTools"))bin_path = Path(default_bin)if not bin_path.is_absolute():    bin_path = (root / bin_path).resolve()
```

This allows for:

1. Absolute paths: `/usr/local/bin/DicomTools`
2. Relative paths from repo root: `cpp/build-debug/DicomTools`
3. Default fallback: `cpp/build/DicomTools`

**Sources:** [interface/adapters/cpp_cli.py L11-L17](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L11-L17)

 [BUILD.md L38](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/BUILD.md#L38-L38)

---

## Integration with Contract System

The C++ backend fully implements the CLI contract specification, with adapter-specific translations for its directory-based output model.

```mermaid
flowchart TD

Request["Request {op, input, output, options}"]
Response["RunResult {ok, returncode, output_files, metadata}"]
ParseOp["Map op to subcommand"]
BuildOutput["output → output_dir"]
BuildCmd["Construct CLI args"]
PredictFiles["Predict output_files"]
Execute["Execute subcommand"]
OutputFiles["Write to output_dir"]
CollectFiles["Collect output_files"]
ParseJSON["parse_json_maybe(stdout)"]
BuildResult["Construct RunResult"]

Request -.-> ParseOp
PredictFiles -.-> Execute
OutputFiles -.-> CollectFiles
Execute -.-> ParseJSON
BuildResult -.-> Response

subgraph subGraph3 ["Response Construction"]
    CollectFiles
    ParseJSON
    BuildResult
    CollectFiles -.-> BuildResult
    ParseJSON -.-> BuildResult
end

subgraph subGraph2 ["DicomTools CLI"]
    Execute
    OutputFiles
    Execute -.-> OutputFiles
end

subgraph subGraph1 ["CppCliAdapter Translation"]
    ParseOp
    BuildOutput
    BuildCmd
    PredictFiles
    ParseOp -.-> BuildOutput
    BuildOutput -.-> BuildCmd
    BuildCmd -.-> PredictFiles
end

subgraph subGraph0 ["Contract Layer"]
    Request
    Response
end
```

### Contract Compliance

**Standard Contract Fields:**

* `op`: Mapped to subcommand (e.g., `anonymize` → `gdcm:anonymize`)
* `input`: Passed as `-i` argument
* `output`: Converted to directory, passed as `-o` argument
* `options`: Interpreted per-operation (e.g., `syntax` for transcode)

**Backend-Specific Behavior:**

* All operations output to directories, not individual files
* File names are predetermined (e.g., `dump.txt`, `preview.pgm`)
* Test operations ignore input/output and run in `cpp/build` directory

**Sources:** [interface/adapters/cpp_cli.py L19-L53](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/adapters/cpp_cli.py#L19-L53)

 [interface/app.py L728-L735](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L728-L735)

---

## Comparison with Other Backends

The C++ backend fills a unique niche in the multi-language toolkit:

| Capability | Python | Rust | **C++** | C# | Java |
| --- | --- | --- | --- | --- | --- |
| Core operations | ✓✓✓ | ✓✓ | ✓✓ | ✓✓ | ✓✓ |
| VTK visualization | ✗ | ✗ | **✓✓✓** | ✗ | ✗ |
| 3D volume rendering | Basic | ✗ | **Advanced** | ✗ | ✗ |
| SR/RT support | Limited | ✗ | **✓** | ✓ | ✓ |
| Network operations | ✓✓ | Basic | ✗ | ✓✓ | ✓✓ |
| Build complexity | Low | Low | **High** | Low | Medium |
| Performance | Medium | High | **High** | Medium | Medium |

**C++ Advantages:**

* Only backend with full VTK integration (15+ visualization operations)
* Native performance for computationally intensive operations
* Access to four major medical imaging libraries
* Advanced 3D rendering and volume processing

**C++ Disadvantages:**

* Complex build dependencies (CMake, DCMTK, GDCM, ITK, VTK)
* Directory-based output model less flexible than file-based
* No network operations (use Python/C#/Java for PACS integration)
* Higher maintenance burden for dependency management

**Sources:** [README.md L8-L13](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/README.md#L8-L13)

 [interface/app.py L149-L187](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/interface/app.py#L149-L187)

Refresh this wiki

Last indexed: 5 January 2026 ([c7b4cb](https://github.com/ThalesMMS/Dicom-Tools/commit/c7b4cbd8))

### On this page

* [C++ Backend](#4.3-c-backend)
* [Purpose and Scope](#4.3-purpose-and-scope)
* [Architecture Overview](#4.3-architecture-overview)
* [Library Roles and Capabilities](#4.3-library-roles-and-capabilities)
* [Build System](#4.3-build-system)
* [Build Configuration](#4.3-build-configuration)
* [Build Commands](#4.3-build-commands)
* [CLI Structure and Adapter Integration](#4.3-cli-structure-and-adapter-integration)
* [Command Building Logic](#4.3-command-building-logic)
* [Output Directory Behavior](#4.3-output-directory-behavior)
* [VTK Visualization Capabilities](#4.3-vtk-visualization-capabilities)
* [VTK Operations Catalog](#4.3-vtk-operations-catalog)
* [VTK Command Mapping](#4.3-vtk-command-mapping)
* [Testing Infrastructure](#4.3-testing-infrastructure)
* [Test Organization](#4.3-test-organization)
* [Test Operations in the Contract](#4.3-test-operations-in-the-contract)
* [Running Tests](#4.3-running-tests)
* [Operation Reference](#4.3-operation-reference)
* [Core DICOM Operations](#4.3-core-dicom-operations)
* [Transcode Syntax Options](#4.3-transcode-syntax-options)
* [Environment Configuration](#4.3-environment-configuration)
* [Binary Path Resolution](#4.3-binary-path-resolution)
* [Integration with Contract System](#4.3-integration-with-contract-system)
* [Contract Compliance](#4.3-contract-compliance)
* [Comparison with Other Backends](#4.3-comparison-with-other-backends)

Ask Devin about Dicom-Tools
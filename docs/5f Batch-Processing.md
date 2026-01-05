# Batch Processing

> **Relevant source files**
> * [python/tests/test_anonymize_dicom.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_anonymize_dicom.py)
> * [python/tests/test_batch_process.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py)
> * [python/tests/test_convert_to_image.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_convert_to_image.py)
> * [python/tests/test_core_modules.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_core_modules.py)
> * [python/tests/test_extract_metadata.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_extract_metadata.py)
> * [python/tests/test_modify_tags.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_modify_tags.py)
> * [python/tests/test_organize_dicom.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_organize_dicom.py)
> * [python/tests/test_pixel_stats.py](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_pixel_stats.py)

This page documents the batch processing capabilities for handling multiple DICOM files in a single operation. Batch processing includes automated file discovery, bulk decompression, anonymization, image conversion, and validation operations.

For individual file operations, see [Core File Operations](#5.1), [Image Conversion and Processing](#5.2), and [Tag Modification and Anonymization](#5.3). For organizing DICOM files by hierarchy, see the organization functions in the Python backend.

**Sources:** [python/tests/test_batch_process.py L1-L263](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L1-L263)

---

## Overview

The batch processing system provides efficient bulk operations on collections of DICOM files. All batch operations are implemented in the Python backend through the `DICOM_reencoder.batch_process` module.

### Core Capabilities

| Function | Purpose | Output Naming |
| --- | --- | --- |
| `find_dicom_files()` | Discovers DICOM files in directories | N/A (returns list) |
| `decompress_batch()` | Decompresses transfer syntaxes | `*_decompressed.dcm` |
| `anonymize_batch()` | Removes PHI from multiple files | `*_anonymized.dcm` |
| `convert_batch()` | Exports to image formats | `*.png`, `*.jpg` |
| `validate_batch()` | Validates DICOM conformance | Console output |
| `list_files()` | Displays file metadata | Console output |

**Sources:** [python/tests/test_batch_process.py L14-L21](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L14-L21)

---

## Batch Processing Architecture

The following diagram illustrates how batch operations build upon individual file operations:

```mermaid
flowchart TD

Input["Input: Directory or File List"]
FindFiles["find_dicom_files()"]
Recursive["Recursive Search Option"]
Filter["Extension Filtering (.dcm, .DCM, .dicom, no ext)"]
Decompress["decompress_batch()"]
Anonymize["anonymize_batch()"]
Convert["convert_batch()"]
Validate["validate_batch()"]
List["list_files()"]
DecompressOne["decompress_file() (per-file)"]
AnonymizeOne["anonymize_dicom() (per-file)"]
ConvertOne["convert_dicom_to_image() (per-file)"]
ValidateOne["validate_file() (per-file)"]
OutputDir["Output Directory (configurable)"]
Suffix["Filename Suffixes (_decompressed, _anonymized)"]
Format["Format Selection (png, jpg for conversion)"]

Input -.-> FindFiles
Decompress -.-> DecompressOne
Anonymize -.-> AnonymizeOne
Convert -.-> ConvertOne
Validate -.-> ValidateOne
DecompressOne -.-> OutputDir
AnonymizeOne -.-> OutputDir
ConvertOne -.-> OutputDir
Filter -.-> BatchOps

subgraph Output ["Output Management"]
    OutputDir
    Suffix
    Format
    OutputDir -.-> Suffix
    OutputDir -.-> Format
end

subgraph IndividualOps ["Individual Operation Layer"]
    DecompressOne
    AnonymizeOne
    ConvertOne
    ValidateOne
end

subgraph BatchOps ["Batch Operation Layer"]
    Decompress
    Anonymize
    Convert
    Validate
    List
end

subgraph Discovery ["File Discovery Layer"]
    FindFiles
    Recursive
    Filter
    FindFiles -.-> Recursive
    FindFiles -.-> Filter
end
```

**Sources:** [python/tests/test_batch_process.py L1-L263](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L1-L263)

---

## File Discovery System

### Finding DICOM Files

The `find_dicom_files()` function discovers DICOM files in directories with support for recursive traversal and flexible extension matching:

```mermaid
flowchart TD

Start["find_dicom_files(directory, recursive)"]
Shallow["Shallow Scan (recursive=False)"]
Deep["Recursive Scan (recursive=True)"]
DcmExt[".dcm extension"]
DcmUpper[".DCM extension"]
DicomExt[".dicom extension"]
NoExt["No extension (DICOM magic number check)"]
MagicCheck["Check DICOM magic bytes (DICM at offset 128)"]
Readable["File readability check"]
Output["List of valid DICOM file paths"]

NoExt -.-> MagicCheck
Readable -.-> Output
Start -.-> ScanModes
Shallow -.-> ExtensionHandling
Deep -.-> ExtensionHandling
DcmExt -.-> Validation
DcmUpper -.-> Validation
DicomExt -.-> Validation

subgraph Validation ["File Validation"]
    MagicCheck
    Readable
    MagicCheck -.-> Readable
end

subgraph ExtensionHandling ["Extension Detection"]
    DcmExt
    DcmUpper
    DicomExt
    NoExt
end

subgraph ScanModes ["Scanning Modes"]
    Shallow
    Deep
end
```

**Key Features:**

* **Recursive Search**: Traverses subdirectories when `recursive=True` [python/tests/test_batch_process.py L36-L48](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L36-L48)
* **Extension Tolerance**: Accepts `.dcm`, `.DCM`, `.dicom`, and files without extensions [python/tests/test_batch_process.py L50-L73](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L50-L73)
* **Content Validation**: Verifies DICOM magic bytes for extensionless files
* **Cross-Platform**: Handles path separators correctly on all platforms

**Sources:** [python/tests/test_batch_process.py L24-L74](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L24-L74)

---

## Batch Decompression

### Overview

The `decompress_batch()` function converts compressed DICOM files to explicit VR little endian transfer syntax:

```mermaid
flowchart TD

Success["Successfully decompressed files"]
Skipped["Already uncompressed files"]
Errors["Error reports"]
Input["Input: List of file paths"]
Iterate["Iterate over files"]
LoadDS["load_dataset(file)"]
CheckTS["Check TransferSyntaxUID"]
Decompress["Decompress if compressed"]
SaveDS["save_dataset(ds, output)"]
HasOutputDir["output_dir specified?"]
DefaultLoc["Same directory as input"]
CustomLoc["Custom output directory"]
Naming["Append '_decompressed.dcm'"]

Input -.-> Iterate
SaveDS -.->|"Yes"| HasOutputDir
Naming -.-> Results

subgraph OutputOptions ["Output Configuration"]
    HasOutputDir
    DefaultLoc
    CustomLoc
    Naming
    HasOutputDir -.->|"No"| CustomLoc
    HasOutputDir -.-> DefaultLoc
    CustomLoc -.-> Naming
    DefaultLoc -.-> Naming
end

subgraph Processing ["Decompression Processing"]
    Iterate
    LoadDS
    CheckTS
    Decompress
    SaveDS
    Iterate -.-> LoadDS
    LoadDS -.-> CheckTS
    CheckTS -.-> Decompress
    Decompress -.-> SaveDS
end

subgraph Results ["Results"]
    Success
    Skipped
    Errors
end
```

### Usage Patterns

**With Output Directory:**

```
decompress_batch(file_paths, output_dir="/path/to/output")# Creates: /path/to/output/file1_decompressed.dcm#          /path/to/output/file2_decompressed.dcm
```

**Without Output Directory:**

```
decompress_batch(file_paths, output_dir=None)# Prints decompression status to console
```

**Sources:** [python/tests/test_batch_process.py L76-L106](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L76-L106)

---

## Batch Anonymization

### Overview

The `anonymize_batch()` function applies PHI removal to multiple files, maintaining consistency across series:

```mermaid
flowchart TD

SamePatient["Same PatientID → Same anonymous ID"]
SameStudy["Consistent StudyInstanceUID"]
SameSeries["Consistent SeriesInstanceUID"]
Input["Input: List of file paths"]
CollectIDs["Collect PatientID from all files"]
GenerateHash["generate_anonymous_id(patient_id)"]
MapIDs["Build consistent ID mapping"]
Iterate["Iterate over files"]
LoadDS["load_dataset(file)"]
ApplyAnon["anonymize_dicom(file, output)"]
RemovePHI["Remove patient identifying tags"]
RegenerateUIDs["Regenerate UIDs consistently"]
ShiftDates["Shift dates consistently"]
OutputDir["Output directory"]
Naming["Append '_anonymized.dcm'"]
Preserve["Preserve pixel data and metadata"]

Input -.-> CollectIDs
MapIDs -.-> Iterate
ShiftDates -.-> OutputDir
RemovePHI -.-> Consistency
RegenerateUIDs -.-> Consistency

subgraph Output ["Output Generation"]
    OutputDir
    Naming
    Preserve
    OutputDir -.-> Naming
    Naming -.-> Preserve
end

subgraph Processing ["Anonymization Processing"]
    Iterate
    LoadDS
    ApplyAnon
    RemovePHI
    RegenerateUIDs
    ShiftDates
    Iterate -.-> LoadDS
    LoadDS -.-> ApplyAnon
    ApplyAnon -.-> RemovePHI
    RemovePHI -.-> RegenerateUIDs
    RegenerateUIDs -.-> ShiftDates
end

subgraph IDMapping ["Patient ID Mapping"]
    CollectIDs
    GenerateHash
    MapIDs
    CollectIDs -.-> GenerateHash
    GenerateHash -.-> MapIDs
end

subgraph Consistency ["Cross-File Consistency"]
    SamePatient
    SameStudy
    SameSeries
end
```

### Anonymization Guarantees

The batch anonymization maintains critical consistency across files:

| Property | Guarantee |
| --- | --- |
| **Patient ID** | Same original ID → Same anonymous ID |
| **Study UID** | Files from same study → Same new UID |
| **Series UID** | Files from same series → Same new UID |
| **Date Shift** | All dates shifted by consistent offset |
| **Pixel Data** | Preserved exactly |
| **Technical Parameters** | Preserved (KVP, SliceThickness, etc.) |

**Example Consistency Test:**

```
# All files in a series get same anonymous PatientIDanonymize_batch(series_paths, output_dir="anonymized/")anon_files = list(Path("anonymized/").glob("*.dcm"))patient_ids = {pydicom.dcmread(f).PatientID for f in anon_files}assert len(patient_ids) == 1  # All have same ID
```

**Sources:** [python/tests/test_batch_process.py L108-L154](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L108-L154)

 [python/tests/test_anonymize_dicom.py L312-L327](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_anonymize_dicom.py#L312-L327)

---

## Batch Image Conversion

### Overview

The `convert_batch()` function exports DICOM pixel data to standard image formats:

```mermaid
flowchart TD

PNG["PNG files (lossless)"]
JPEG["JPEG files (lossy)"]
Skipped["Skipped (no pixel data)"]
Format["output_format parameter (png, jpg, jpeg)"]
Window["Optional window/level (window_center, window_width)"]
Frame["Optional frame_number (for multiframe)"]
Input["Input: List of file paths"]
Iterate["Iterate over files"]
LoadDS["load_dataset(file)"]
ExtractPixels["Extract pixel_array"]
ApplyWindow["Apply windowing (auto or manual)"]
ConvertImage["convert_dicom_to_image()"]
SaveImage["Save as PNG/JPEG"]
BaseName["Extract base filename"]
RemoveExt["Remove .dcm extension"]
AddFormat["Add image extension (.png or .jpg)"]

Input -.-> Configuration
Configuration -.-> Iterate
SaveImage -.-> OutputNaming
AddFormat -.-> Results

subgraph OutputNaming ["Output Naming"]
    BaseName
    RemoveExt
    AddFormat
    BaseName -.-> RemoveExt
    RemoveExt -.-> AddFormat
end

subgraph Processing ["Conversion Processing"]
    Iterate
    LoadDS
    ExtractPixels
    ApplyWindow
    ConvertImage
    SaveImage
    Iterate -.-> LoadDS
    LoadDS -.-> ExtractPixels
    ExtractPixels -.-> ApplyWindow
    ApplyWindow -.-> ConvertImage
    ConvertImage -.-> SaveImage
end

subgraph Results ["Results"]
    PNG
    JPEG
    Skipped
end

subgraph Configuration ["Conversion Configuration"]
    Format
    Window
    Frame
end
```

### Format Selection

| Format | Use Case | Quality | Size | Notes |
| --- | --- | --- | --- | --- |
| **PNG** | Archival, web display | Lossless | Larger | Default format |
| **JPEG** | Web thumbnails | Lossy | Smaller | Quality parameter available |

### Windowing Behavior

The conversion applies window/level transformation to map pixel values to display range:

1. **Auto-windowing** (default): Uses median and IQR from pixel data [python/tests/test_convert_to_image.py L59-L87](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_convert_to_image.py#L59-L87)
2. **Manual windowing**: Accepts `window_center` and `window_width` parameters [python/tests/test_convert_to_image.py L109-L122](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_convert_to_image.py#L109-L122)
3. **DICOM metadata**: Falls back to WindowCenter/WindowWidth tags if present

**Sources:** [python/tests/test_batch_process.py L156-L189](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L156-L189)

 [python/tests/test_convert_to_image.py L1-L184](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_convert_to_image.py#L1-L184)

---

## Batch Validation

### Overview

The `validate_batch()` function performs conformance checking on multiple DICOM files:

```mermaid
flowchart TD

Input["Input: List of file paths"]
Iterate["Iterate over files"]
ReadFile["Read DICOM file"]
CheckMagic["Verify DICOM magic bytes"]
ParseMeta["Parse file meta information"]
CheckRequired["Check required tags (SOPClassUID, SOPInstanceUID)"]
ValidateTS["Validate TransferSyntaxUID"]
CheckPixels["Verify pixel data consistency"]
Valid["Valid files"]
InvalidStructure["Invalid DICOM structure"]
MissingTags["Missing required tags"]
CorruptPixels["Corrupt pixel data"]
Summary["Validation summary"]
PerFile["Per-file status"]
ErrorDetails["Detailed error messages"]
Statistics["Overall statistics"]

Input -.-> Iterate
Valid -.-> PerFile
InvalidStructure -.-> ErrorDetails
MissingTags -.-> ErrorDetails
CorruptPixels -.-> ErrorDetails
CheckPixels -.-> Reporting
Statistics -.-> Output

subgraph Output ["Console Output"]
    PerFile
    ErrorDetails
    Statistics
    PerFile -.-> Statistics
    ErrorDetails -.-> Statistics
end

subgraph Reporting ["Validation Reporting"]
    Valid
    InvalidStructure
    MissingTags
    CorruptPixels
    Summary
end

subgraph Validation ["Validation Checks"]
    Iterate
    ReadFile
    CheckMagic
    ParseMeta
    CheckRequired
    ValidateTS
    CheckPixels
    Iterate -.-> ReadFile
    ReadFile -.-> CheckMagic
    CheckMagic -.-> ParseMeta
    ParseMeta -.-> CheckRequired
    CheckRequired -.-> ValidateTS
    ValidateTS -.-> CheckPixels
end
```

### Validation Errors Detected

The validation process identifies:

* **Structural Errors**: Invalid DICOM file structure, missing magic bytes
* **Tag Errors**: Missing required tags (SOPClassUID, SOPInstanceUID, StudyInstanceUID, SeriesInstanceUID)
* **Transfer Syntax Errors**: Invalid or unsupported transfer syntax UIDs
* **Pixel Data Errors**: Inconsistent pixel data dimensions or bit depth
* **VR Errors**: Incorrect value representation for tags

**Sources:** [python/tests/test_batch_process.py L191-L218](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L191-L218)

---

## File Listing and Metadata Display

### Overview

The `list_files()` function displays comprehensive metadata for multiple files:

```mermaid
flowchart TD

Header["File path header"]
Formatted["Formatted metadata output"]
Separator["Visual separators"]
Input["Input: List of file paths"]
Iterate["Iterate over files"]
LoadDS["load_dataset(file)"]
ExtractMeta["Extract key metadata"]
Patient["Patient Information (Name, ID, Birth Date)"]
Study["Study Information (Description, Date, UID)"]
Series["Series Information (Modality, Number, UID)"]
Image["Image Information (Rows, Columns, Frames)"]

Input -.-> Iterate
ExtractMeta -.-> Categories
Patient -.-> Display
Study -.-> Display
Series -.-> Display
Image -.-> Display

subgraph Categories ["Metadata Categories"]
    Patient
    Study
    Series
    Image
end

subgraph Processing ["Metadata Extraction"]
    Iterate
    LoadDS
    ExtractMeta
    Iterate -.-> LoadDS
    LoadDS -.-> ExtractMeta
end

subgraph Display ["Console Display"]
    Header
    Formatted
    Separator
end
```

### Metadata Fields Displayed

The listing includes (when present):

**Patient Level:**

* PatientName
* PatientID
* PatientBirthDate
* PatientSex

**Study Level:**

* StudyDescription
* StudyDate
* StudyTime
* StudyInstanceUID

**Series Level:**

* SeriesDescription
* SeriesNumber
* Modality
* SeriesInstanceUID

**Image Level:**

* Rows, Columns
* NumberOfFrames
* BitsAllocated, BitsStored
* PhotometricInterpretation
* TransferSyntaxUID

**Sources:** [python/tests/test_batch_process.py L221-L263](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L221-L263)

---

## Integration with CLI and Adapters

The batch processing functions integrate with the CLI contract system through wrapper commands:

```mermaid
flowchart TD

FileList["List of processed files"]
ErrorLog["Error messages"]
Metadata["Operation metadata"]
BatchCmd["dicom-tools batch-anonymize dicom-tools batch-convert dicom-tools batch-validate"]
PythonAdapter["PythonCliAdapter"]
BuildCmd["_build_cmd()"]
ParseResult["parse_json_maybe()"]
FindDICOM["find_dicom_files()"]
AnonymizeBatch["anonymize_batch()"]
ConvertBatch["convert_batch()"]
ValidateBatch["validate_batch()"]

CLILayer -.-> AdapterLayer
AdapterLayer -.-> BuildCmd
BuildCmd -.-> BatchModule
AnonymizeBatch -.-> Results
ConvertBatch -.-> Results
ValidateBatch -.-> Results
Results -.-> ParseResult
ParseResult -.-> CLILayer

subgraph BatchModule ["batch_process Module"]
    FindDICOM
    AnonymizeBatch
    ConvertBatch
    ValidateBatch
    FindDICOM -.-> AnonymizeBatch
    FindDICOM -.-> ConvertBatch
    FindDICOM -.-> ValidateBatch
end

subgraph AdapterLayer ["Adapter Layer"]
    PythonAdapter
    BuildCmd
    ParseResult
end

subgraph Results ["Result Handling"]
    FileList
    ErrorLog
    Metadata
end

subgraph CLILayer ["CLI Command Layer"]
    BatchCmd
end
```

### Batch Operation Request Format

When invoked through the CLI contract, batch operations follow this request structure:

```
{  "op": "batch_anonymize",  "input": "/path/to/directory",  "output": "/path/to/output",  "options": {    "recursive": true,    "patient_prefix": "ANON"  }}
```

**Response Format:**

```
{  "ok": true,  "returncode": 0,  "output_files": [    "/path/to/output/file1_anonymized.dcm",    "/path/to/output/file2_anonymized.dcm"  ],  "metadata": {    "files_processed": 2,    "files_skipped": 0,    "errors": []  }}
```

**Sources:** [python/tests/test_batch_process.py L1-L263](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L1-L263)

---

## Error Handling and Recovery

Batch operations implement robust error handling to continue processing despite individual file failures:

```mermaid
flowchart TD

Success["Successful operations"]
Failed["Failed operations"]
Summary["Summary statistics"]
Start["Start batch operation"]
TryCatch["Try-catch per file"]
LogError["Log error details"]
Continue["Continue with next file"]
CollectErrors["Collect all errors"]
ReadError["File read errors"]
PermissionError["Permission denied"]
CorruptFile["Corrupt DICOM file"]
OutOfMemory["Out of memory"]
WriteError["Output write error"]
SkipFile["Skip problematic file"]
Retry["Retry with alternative method"]
Partial["Save partial results"]
Report["Report in summary"]

Start -.-> TryCatch
ReadError -.-> LogError
PermissionError -.-> LogError
CorruptFile -.-> LogError
OutOfMemory -.-> LogError
WriteError -.-> LogError
SkipFile -.-> CollectErrors
Retry -.-> Continue
Partial -.-> Continue
TryCatch -.-> ErrorTypes
LogError -.-> Recovery
CollectErrors -.-> FinalReport
Continue -.-> FinalReport

subgraph Recovery ["Recovery Actions"]
    SkipFile
    Retry
    Partial
    Report
end

subgraph ErrorTypes ["Common Error Types"]
    ReadError
    PermissionError
    CorruptFile
    OutOfMemory
    WriteError
end

subgraph ErrorHandling ["Error Handling Strategy"]
    TryCatch
    LogError
    Continue
    CollectErrors
end

subgraph FinalReport ["Final Reporting"]
    Success
    Failed
    Summary
end
```

### Error Handling Behavior

| Error Type | Batch Response | Individual File | Affects Completion |
| --- | --- | --- | --- |
| **Read Error** | Log and continue | Skipped | No |
| **Corrupt DICOM** | Log and continue | Skipped | No |
| **Permission Error** | Log and continue | Skipped | No |
| **Out of Memory** | Abort batch | All remaining skipped | Yes |
| **Output Write Error** | Log and continue | Skipped | No |

**Sources:** [python/tests/test_batch_process.py L203-L218](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L203-L218)

---

## Performance Considerations

### Memory Management

Batch operations process files sequentially to manage memory usage:

* **Sequential Processing**: Files loaded one at a time [python/tests/test_batch_process.py L111-L122](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L111-L122)
* **Dataset Cleanup**: Each dataset released after processing
* **Pixel Array Handling**: Large pixel arrays not kept in memory simultaneously

### Optimization Strategies

**For Large Batches:**

1. Use recursive file discovery once, store paths
2. Process in chunks if memory constrained
3. Use output directory to avoid in-place modifications
4. Disable verbose logging for faster execution

**For Series Processing:**

1. Group files by SeriesInstanceUID before processing
2. Maintain UID consistency within series
3. Process series sequentially to ensure consistency

**Sources:** [python/tests/test_batch_process.py L1-L263](https://github.com/ThalesMMS/Dicom-Tools/blob/c7b4cbd8/python/tests/test_batch_process.py#L1-L263)

Refresh this wiki

Last indexed: 5 January 2026 ([c7b4cb](https://github.com/ThalesMMS/Dicom-Tools/commit/c7b4cbd8))

### On this page

* [Batch Processing](#5.6-batch-processing)
* [Overview](#5.6-overview)
* [Core Capabilities](#5.6-core-capabilities)
* [Batch Processing Architecture](#5.6-batch-processing-architecture)
* [File Discovery System](#5.6-file-discovery-system)
* [Finding DICOM Files](#5.6-finding-dicom-files)
* [Batch Decompression](#5.6-batch-decompression)
* [Overview](#5.6-overview-1)
* [Usage Patterns](#5.6-usage-patterns)
* [Batch Anonymization](#5.6-batch-anonymization)
* [Overview](#5.6-overview-2)
* [Anonymization Guarantees](#5.6-anonymization-guarantees)
* [Batch Image Conversion](#5.6-batch-image-conversion)
* [Overview](#5.6-overview-3)
* [Format Selection](#5.6-format-selection)
* [Windowing Behavior](#5.6-windowing-behavior)
* [Batch Validation](#5.6-batch-validation)
* [Overview](#5.6-overview-4)
* [Validation Errors Detected](#5.6-validation-errors-detected)
* [File Listing and Metadata Display](#5.6-file-listing-and-metadata-display)
* [Overview](#5.6-overview-5)
* [Metadata Fields Displayed](#5.6-metadata-fields-displayed)
* [Integration with CLI and Adapters](#5.6-integration-with-cli-and-adapters)
* [Batch Operation Request Format](#5.6-batch-operation-request-format)
* [Error Handling and Recovery](#5.6-error-handling-and-recovery)
* [Error Handling Behavior](#5.6-error-handling-behavior)
* [Performance Considerations](#5.6-performance-considerations)
* [Memory Management](#5.6-memory-management)
* [Optimization Strategies](#5.6-optimization-strategies)

Ask Devin about Dicom-Tools
# DICOM Tools & Testing Grounds

A comprehensive Python repository serving two main purposes:
1.  **Functional Toolkit:** A suite of 20+ command-line interface (CLI) tools for inspecting, modifying, anonymizing, and managing DICOM files, plus a web interface.
2.  **Testing Grounds:** A collection of isolated scripts to demonstrate and verify the capabilities of major Python DICOM libraries (`pydicom`, `pynetdicom`, `gdcm`, `SimpleITK`, `dicom-numpy`).

## 🛠 Installation

To use the CLI tools or run the tests, install the package and its dependencies:

```bash
# Clone the repository and enter the Python package
git clone https://github.com/ThalesMMS/Dicom-Tools.git
cd Dicom-Tools/python

# Install in editable mode (recommended for development)
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

*Note: `python-gdcm` might need to be installed separately depending on your OS, though it is included in the installation steps if available via pip.*

## 🖥️ CLI Tools Usage

Once installed, the following commands are available globally in your terminal:

### Inspection & Analysis
- `dicom-info <file>`: Quick summary of a DICOM file.
- `dicom-extract-metadata <file>`: Detailed metadata extraction.
- `dicom-pixel-stats <file>`: Analyze pixel value statistics and histograms.
- `dicom-compare <file1> <file2>`: Compare tags between two files.
- `dicom-validate <file>`: Validate compliance and data integrity.
- `dicom-search -d <dir> ...`: Search for files matching specific metadata criteria.
- `dicom-volume <dir>`: Build a 3D NumPy volume and JSON metadata from a slice directory (powered by `dicom-numpy`).

### Manipulation & Processing
- `dicom-anonymize <input> [output]`: Remove PHI (HIPAA-compliant).
- `dicom-to-image <file> [format]`: Convert DICOM to PNG/JPEG.
- `dicom-modify <file> -t Tag=Value`: Modify tags interactively or in batch.
- `dicom-reencode <file>`: Rewrite file with Explicit VR Little Endian.
- `dicom-decompress <file>`: Decompress pixel data.
- `dicom-transcode <file> --syntax ...`: Change transfer syntax using GDCM (e.g., decompress to Explicit VR).
- `dicom-to-nifti <dir>`: Export a DICOM series to `.nii`/`.nii.gz` with spacing/orientation preserved (SimpleITK).
- `dicom-split-multiframe <file>`: Split multi-frame files into single frames.
- `dicom-organize -s <src> -d <dst> ...`: Organize files into folders (Patient/Study/Series).

### PACS Networking
- `dicom-query ...`: Perform C-FIND queries against a PACS server.
- `dicom-retrieve ...`: Retrieve studies via C-MOVE or C-GET.
- `dicom-echo [host] --port <p>`: Lightweight C-ECHO (DICOM ping) to verify connectivity.

### Web Interface
- `dicom-web`: Launch a local Flask web server for visual interaction.

### Notes on optional dependencies
- `dicom-volume` requires `dicom-numpy`.
- `dicom-to-nifti` requires `SimpleITK`.
- `dicom-transcode` requires `gdcm`.

Install all optional tooling with:
```bash
pip install -r requirements.txt
# or
pip install "dicom-tools[extra]"
```

## 🧪 Library Testing Grounds

The `tests/` directory exercises key features of each library:

- **pydicom:** uncommon VRs (UN/UR/AT/OF/OD), private tags, DICOM JSON model roundtrip, deferred reads, sequences/nested datasets, Basic Text SR, UTF-8 character sets, multi-frame functional groups, secondary capture creation, SEG generation.
- **pynetdicom:** in-process C-ECHO, C-FIND (StudyRoot + MWL), C-MOVE with internal C-STORE, C-GET (skips if storage contexts aren’t accepted), timeout/failure handling, optional TLS echo, Storage Commitment (N-ACTION) and MPPS (N-CREATE/N-SET), concurrent C-STORE + C-FIND associations.
- **GDCM:** transfer syntax transcoding (RLE/JPEG2000), writer round-trip with tag edits, DICOMDIR generation (skips if the generator is unavailable), segmentation readback into NumPy (isolated in a subprocess and skipped if the local python-gdcm build aborts—macOS + Python 3.14 wheels are known to be fragile here).
- **SimpleITK:** series IO, basic registration, masking/label stats, segmentation filters (region growing/watershed), 4D label stats aggregation, multi-label exports to DICOM series, NIfTI roundtrip back to DICOM (skips if DICOM writer not supported).
- **dicom-numpy:** slice ordering edge cases, irregular spacing tolerance, duplicates, multi-echo stacking, affine comparison against SimpleITK, NIfTI export with histogram/summary validation.

Run the full suite (uses synthetic fixtures by default):

```bash
pytest -q
```

Notes:
- Some tests skip gracefully if optional libs or DICOM series writing aren’t available.
- Network tests run entirely in-process and do not require external PACS.

## Structure

*   `DICOM_reencoder/`: Source code for the CLI tools package.
*   `tests/`: Unit tests and library verification scripts.
*   `input/`: Local directory for test images (ignored by git).
*   `output/`: Local directory for processing results (ignored by git).

## License
MIT

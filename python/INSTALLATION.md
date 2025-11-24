# Installation Guide - DICOM Tools

English-only guide for installing the CLI tools, optional features, and validating that everything works.

## Installation Methods

### 1. pip (recommended)
```bash
# Install directly from GitHub
pip install git+https://github.com/ThalesMMS/Dicom-Tools.git

# Or install from a local checkout
pip install .

# Development (editable) install
pip install -e .
```

### 2. Manual setup
```bash
git clone https://github.com/ThalesMMS/Dicom-Tools.git
cd Dicom-Tools

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
pip install -e .
```

### 3. Optional feature sets
```bash
# Everything for development + optional libs (gdcm, SimpleITK, dicom-numpy)
pip install -e ".[dev]"

# Only web extras
pip install -e ".[web]"

# Only networking extras
pip install -e ".[networking]"

# All optional runtime extras
pip install -e ".[extra]"
```

## Verify the Installation

### CLI commands
```bash
dicom-info --help
dicom-query --help
dicom-web --help
dicom-volume --help
dicom-to-nifti --help
dicom-transcode --help
```

### Python import
```python
import DICOM_reencoder
from DICOM_reencoder import anonymize_dicom
```

## Available CLI Commands

### Inspection & Metadata
- `dicom-extract-metadata` – detailed metadata dump
- `dicom-info` – quick summary
- `dicom-compare` – compare two files
- `dicom-pixel-stats` – pixel statistics
- `dicom-validate` – compliance/integrity checks
- `dicom-volume` – build a 3D NumPy volume + JSON metadata (dicom-numpy)

### Conversion
- `dicom-reencode` – recode transfer syntax
- `dicom-decompress` – decompress DICOM
- `dicom-to-image` – convert to PNG/JPEG
- `dicom-transcode` – change transfer syntax with GDCM
- `dicom-to-nifti` – export series to NIfTI (SimpleITK)
- `dicom-split-multiframe` – split multi-frame

### Privacy
- `dicom-anonymize` – anonymize files

### Modification & Organization
- `dicom-modify` – edit tags
- `dicom-organize` – sort into folders
- `dicom-search` – search by criteria
- `dicom-batch` – batch processing

### Networking
- `dicom-query` – C-FIND for PACS
- `dicom-retrieve` – C-MOVE/C-GET from PACS
- `dicom-echo` – C-ECHO (ping) for quick connectivity checks

### Web Interface
- `dicom-web` – start the Flask UI

## Quick Usage Examples

```bash
# Start the web UI
dicom-web --host 0.0.0.0 --port 8080

# Build a 3D volume and metadata from a folder
dicom-volume ./input/series1 -o ./output/series1.npy

# Export a series to NIfTI
dicom-to-nifti ./input/series1 -o ./output/series1.nii.gz

# Transcode to Explicit VR Little Endian
dicom-transcode input.dcm --syntax explicit -o output_explicit.dcm

# PACS queries
dicom-query -H pacs.example.com -p 11112 --patient-name "DOE*"
dicom-retrieve -H pacs.example.com -p 11112 --study-uid 1.2.3.4.5 -o ./studies
```

## Dependencies

### Required
- Python >= 3.9
- pydicom >= 2.3.0
- numpy >= 1.20.0
- Pillow >= 9.0.0
- pynetdicom >= 2.0.0
- flask >= 2.0.0
- flask-cors >= 3.0.0

### Optional (for new features)
- gdcm >= 3.0.0 (transfer syntax changes)
- SimpleITK >= 2.2.0 (NIfTI export)
- dicom-numpy >= 0.5.0 (3D volume builder)

## Troubleshooting

- **Command not found:** reinstall with `pip install --force-reinstall .` and ensure your Python bin directory is on `PATH`.
- **Missing optional library:** install with `pip install -r requirements.txt` or `pip install "dicom-tools[extra]"`.
- **PACS connectivity issues:** run `dicom-echo <host> --port <p>` to verify that the port accepts associations.

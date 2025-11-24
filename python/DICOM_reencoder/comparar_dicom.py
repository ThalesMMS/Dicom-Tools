#
# comparar_dicom.py
# Dicom-Tools-py
#
# Compares key DICOM metadata fields between two files to highlight differences quickly.
#
# Thales Matheus Mendonça Santos - November 2025

import pydicom
import os
import sys

def extract_metadata(path):
    try:
        dataset = pydicom.dcmread(path, stop_before_pixels=True, force=True)
        # Collect a focused subset of tags to keep output readable
        return {
            "File": os.path.basename(path),
            "SOPClassUID": dataset.get("SOPClassUID", "N/A"),
            "TransferSyntaxUID": dataset.file_meta.get("TransferSyntaxUID", "N/A"),
            "PhotometricInterpretation": dataset.get("PhotometricInterpretation", "N/A"),
            "BitsAllocated": dataset.get("BitsAllocated", "N/A"),
            "BitsStored": dataset.get("BitsStored", "N/A"),
            "HighBit": dataset.get("HighBit", "N/A"),
            "PixelRepresentation": dataset.get("PixelRepresentation", "N/A"),
            "Modality": dataset.get("Modality", "N/A"),
            "ImageType": dataset.get("ImageType", "N/A"),
        }
    except Exception as error:
        print(f"Error reading {path}: {error}")
        return None

def compare_metadata(metadata1, metadata2):
    keys = metadata1.keys()
    print(f"\n{'Field':<30} {'1.dcm':<50} {'2.dcm'}")
    print("-" * 110)
    for key in keys:
        value1 = str(metadata1[key])
        value2 = str(metadata2[key])
        marker = " <-- DIFFERENT" if value1 != value2 else ""
        # Align columns for quick visual diffing when scanning terminal output
        print(f"{key:<30} {value1:<50} {value2}{marker}")

def main():
    if len(sys.argv) > 2:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
    else:
        file1 = "1.dcm"
        file2 = "2.dcm"

    if not (os.path.exists(file1) and os.path.exists(file2)):
        print(f"Error: Make sure '{file1}' and '{file2}' are in the same folder as the script.")
        sys.exit(1)

    metadata1 = extract_metadata(file1)
    metadata2 = extract_metadata(file2)

    if metadata1 and metadata2:
        compare_metadata(metadata1, metadata2)

if __name__ == "__main__":
    main()

#
# decompress_dicom.py
# Dicom-Tools-py
#
# Decompresses DICOM files to explicit VR little endian to improve viewer compatibility.
#
# Thales Matheus Mendonça Santos - November 2025

import sys
import pydicom
from pydicom.uid import ExplicitVRLittleEndian

def main():
    input_file = "1.dcm"
    output_file = "1_decompressed.dcm"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        # Force reading compressed images
        dataset = pydicom.dcmread(input_file, force=True)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        sys.exit(1)

    # Only run the (potentially expensive) decompress step when the transfer syntax says it's needed
    if dataset.file_meta.TransferSyntaxUID.is_compressed:
        try:
            dataset.decompress()
        except Exception as e:
            print(f"Error decompressing: {e}")
            sys.exit(1)

    # Advertise the uncompressed syntax so downstream viewers open the file correctly
    dataset.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    # Save a new version readable by OsiriX
    dataset.save_as(output_file)
    print(f"Decompressed image saved in: {output_file}")

if __name__ == "__main__":
    main()

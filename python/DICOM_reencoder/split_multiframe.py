#!/usr/bin/env python3
#
# split_multiframe.py
# Dicom-Tools-py
#
# Splits multi-frame DICOM datasets into single-frame files and inspects frame metadata.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Split multi-frame DICOM files into single-frame files.
This script takes a multi-frame DICOM file and creates separate
single-frame DICOM files for each frame.
"""

import pydicom
import sys
import os
import argparse
import numpy as np
from pydicom.uid import generate_uid, ExplicitVRLittleEndian

def split_multiframe(input_file, output_dir=None, prefix=None):
    """
    Split a multi-frame DICOM file into single-frame files.

    Args:
        input_file: Path to input multi-frame DICOM file
        output_dir: Output directory for split files
        prefix: Prefix for output filenames

    Returns:
        Number of frames created
    """
    try:
        # Read the DICOM file
        print(f"\nReading DICOM file: {input_file}")
        dataset = pydicom.dcmread(input_file, force=True)

        # Check if pixel data exists
        if 'PixelData' not in dataset:
            print("Error: No pixel data found in DICOM file.")
            return 0

        # Get pixel array
        pixel_array = dataset.pixel_array

        # Check if it's a multi-frame image
        if len(pixel_array.shape) <= 2:
            print("Error: This is a single-frame image, not multi-frame.")
            print(f"Image dimensions: {pixel_array.shape}")
            return 0

        num_frames = pixel_array.shape[0]
        print(f"Multi-frame image detected: {num_frames} frames")
        print(f"Frame dimensions: {pixel_array.shape[1]} x {pixel_array.shape[2]}")

        # Set output directory
        if output_dir is None:
            base_dir = os.path.dirname(input_file)
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.join(base_dir, f"{base_name}_split")

        os.makedirs(output_dir, exist_ok=True)

        # Set prefix
        if prefix is None:
            prefix = os.path.splitext(os.path.basename(input_file))[0]

        print(f"\nSplitting into: {output_dir}")
        print(f"{'='*80}\n")

        # Keep track of the original series so the resulting files remain grouped logically
        original_series_uid = dataset.get('SeriesInstanceUID', generate_uid())

        # Split frames
        for frame_idx in range(num_frames):
            try:
                # Clone the header so each output frame retains the original metadata
                frame_dataset = dataset.copy()

                # Extract this frame's pixel data
                frame_pixels = pixel_array[frame_idx]

                # Update pixel data
                frame_dataset.PixelData = frame_pixels.tobytes()

                # Update NumberOfFrames (should be 1 for single frame)
                if 'NumberOfFrames' in frame_dataset:
                    frame_dataset.NumberOfFrames = 1

                # Update Instance Number
                frame_dataset.InstanceNumber = frame_idx + 1

                # Generate new SOP Instance UID for each frame
                frame_dataset.SOPInstanceUID = generate_uid()

                # Keep the same Series Instance UID so they appear as one series
                frame_dataset.SeriesInstanceUID = original_series_uid

                # Update file meta information
                if hasattr(frame_dataset, 'file_meta'):
                    # Refresh file meta so each slice is self-contained and uncompressed
                    frame_dataset.file_meta.MediaStorageSOPInstanceUID = frame_dataset.SOPInstanceUID
                    frame_dataset.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

                # Create output filename
                output_file = os.path.join(output_dir, f"{prefix}_frame_{frame_idx+1:04d}.dcm")

                # Save the frame
                frame_dataset.save_as(output_file)

                print(f"  ✓ Frame {frame_idx+1:4d}/{num_frames} -> {os.path.basename(output_file)}")

            except Exception as e:
                print(f"  ✗ Error processing frame {frame_idx+1}: {e}")

        print(f"\n{'='*80}")
        print(f"✓ Split complete!")
        print(f"  Total frames: {num_frames}")
        print(f"  Output directory: {output_dir}")
        print(f"{'='*80}\n")

        return num_frames

    except Exception as e:
        print(f"Error splitting multi-frame DICOM: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 0

def get_frame_info(input_file):
    """
    Display information about frames in a multi-frame DICOM file.

    Args:
        input_file: Path to DICOM file
    """
    try:
        dataset = pydicom.dcmread(input_file, force=True)

        print(f"\n{'='*80}")
        print(f"Multi-frame DICOM Information")
        print(f"{'='*80}")
        print(f"File: {os.path.basename(input_file)}\n")

        if 'PixelData' not in dataset:
            print("No pixel data found.")
            return

        pixel_array = dataset.pixel_array

        if len(pixel_array.shape) <= 2:
            print("This is a single-frame image.")
            print(f"Dimensions: {pixel_array.shape[1]} x {pixel_array.shape[0]}")
        else:
            num_frames = pixel_array.shape[0]
            print(f"Multi-frame image: {num_frames} frames")
            print(f"Frame dimensions: {pixel_array.shape[2]} x {pixel_array.shape[1]}")
            print(f"Total pixel array shape: {pixel_array.shape}")

        # Additional frame-related metadata
        print(f"\nFrame Metadata:")
        frame_fields = [
            'NumberOfFrames',
            'FrameTime',
            'FrameDelay',
            'FrameIncrementPointer',
            'RecommendedDisplayFrameRate'
        ]

        for field in frame_fields:
            if field in dataset:
                print(f"  {field:<30}: {dataset.get(field)}")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"Error reading DICOM file: {e}", file=sys.stderr)

def extract_specific_frames(input_file, frame_numbers, output_dir=None):
    """
    Extract specific frames from a multi-frame DICOM file.

    Args:
        input_file: Path to input DICOM file
        frame_numbers: List of frame numbers to extract (1-based)
        output_dir: Output directory
    """
    try:
        dataset = pydicom.dcmread(input_file, force=True)

        if 'PixelData' not in dataset:
            print("Error: No pixel data found.")
            return 0

        pixel_array = dataset.pixel_array

        if len(pixel_array.shape) <= 2:
            print("Error: This is a single-frame image.")
            return 0

        num_frames = pixel_array.shape[0]
        print(f"\nMulti-frame image: {num_frames} frames")

        # Validate frame numbers
        valid_frames = [f for f in frame_numbers if 1 <= f <= num_frames]
        invalid_frames = [f for f in frame_numbers if f not in valid_frames]

        if invalid_frames:
            print(f"Warning: Invalid frame numbers (will be skipped): {invalid_frames}")

        if not valid_frames:
            print("Error: No valid frame numbers specified.")
            return 0

        # Set output directory
        if output_dir is None:
            base_dir = os.path.dirname(input_file)
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.join(base_dir, f"{base_name}_extracted")

        os.makedirs(output_dir, exist_ok=True)

        print(f"\nExtracting frames: {valid_frames}")
        print(f"Output directory: {output_dir}")
        print(f"{'='*80}\n")

        prefix = os.path.splitext(os.path.basename(input_file))[0]
        extracted_count = 0

        for frame_num in valid_frames:
            frame_idx = frame_num - 1  # Convert to 0-based index

            try:
                frame_dataset = dataset.copy()
                frame_pixels = pixel_array[frame_idx]
                frame_dataset.PixelData = frame_pixels.tobytes()

                if 'NumberOfFrames' in frame_dataset:
                    frame_dataset.NumberOfFrames = 1

                frame_dataset.InstanceNumber = frame_num
                frame_dataset.SOPInstanceUID = generate_uid()

                if hasattr(frame_dataset, 'file_meta'):
                    frame_dataset.file_meta.MediaStorageSOPInstanceUID = frame_dataset.SOPInstanceUID

                output_file = os.path.join(output_dir, f"{prefix}_frame_{frame_num:04d}.dcm")
                frame_dataset.save_as(output_file)

                print(f"  ✓ Frame {frame_num} -> {os.path.basename(output_file)}")
                extracted_count += 1

            except Exception as e:
                print(f"  ✗ Error extracting frame {frame_num}: {e}")

        print(f"\n{'='*80}")
        print(f"✓ Extraction complete! {extracted_count} frames extracted.")
        print(f"{'='*80}\n")

        return extracted_count

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 0

def main():
    parser = argparse.ArgumentParser(
        description='Split multi-frame DICOM files into single-frame files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Split all frames
  %(prog)s multiframe.dcm

  # Split to specific directory
  %(prog)s multiframe.dcm -o ./output

  # Split with custom prefix
  %(prog)s multiframe.dcm --prefix ct_scan

  # Extract specific frames only
  %(prog)s multiframe.dcm --frames 1 5 10 15

  # Show frame information without splitting
  %(prog)s multiframe.dcm --info
        '''
    )

    parser.add_argument('input_file', help='Input multi-frame DICOM file')
    parser.add_argument('-o', '--output-dir', help='Output directory for split files')
    parser.add_argument('--prefix', help='Prefix for output filenames')
    parser.add_argument('--frames', type=int, nargs='+', metavar='N',
                        help='Extract only specific frame numbers (1-based)')
    parser.add_argument('--info', action='store_true',
                        help='Show frame information without splitting')

    args = parser.parse_args()

    # Show info mode
    if args.info:
        get_frame_info(args.input_file)
        return 0

    # Extract specific frames
    if args.frames:
        extract_specific_frames(args.input_file, args.frames, args.output_dir)
    else:
        # Split all frames
        split_multiframe(args.input_file, args.output_dir, args.prefix)

    return 0

if __name__ == "__main__":
    sys.exit(main())

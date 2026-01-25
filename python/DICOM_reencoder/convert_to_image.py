#!/usr/bin/env python3
#
# convert_to_image.py
# Dicom-Tools-py
#
# Converts DICOM pixel data into standard image formats with windowing and frame selection support.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Convert DICOM files to standard image formats (PNG, JPEG).
This script extracts pixel data from DICOM files and saves them as
standard image files with proper windowing applied.
"""

import pydicom
import sys
import os
import numpy as np

def apply_windowing(pixel_array, window_center, window_width):
    """
    Apply window/level to pixel data for proper visualization.

    Args:
        pixel_array: NumPy array of pixel data
        window_center: Window center (level)
        window_width: Window width
    """
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2

    # Apply windowing
    windowed = np.clip(pixel_array, img_min, img_max)

    # Normalize to 0-255
    windowed = ((windowed - img_min) / (img_max - img_min) * 255.0)

    return windowed.astype(np.uint8)

def auto_window(pixel_array):
    """
    Automatically determine window settings based on pixel data statistics.
    """
    # Use median/percentiles to avoid being skewed by outliers
    window_center = int(np.median(pixel_array))
    window_width = int(np.percentile(pixel_array, 95) - np.percentile(pixel_array, 5))

    return window_center, window_width

def convert_dicom_to_image(input_file, output_file=None, output_format='png',
                          window_center=None, window_width=None, frame_number=0):
    """
    Convert a DICOM file to PNG or JPEG.

    Args:
        input_file: Path to input DICOM file
        output_file: Path to output image file (default: auto-generated)
        output_format: Output format ('png' or 'jpeg')
        window_center: Window center for display (None for auto)
        window_width: Window width for display (None for auto)
        frame_number: Frame number for multi-frame images (default: 0)
    """
    try:
        # Pillow is required for saving images
        try:
            from PIL import Image
        except ImportError:
            print("Error: Pillow library is required for image conversion.")
            print("Install it with: pip install Pillow")
            return None

        # Read the DICOM file
        print(f"\nReading DICOM file: {input_file}")
        dataset = pydicom.dcmread(input_file, force=True)

        # Check if pixel data exists
        if 'PixelData' not in dataset:
            print("Error: No pixel data found in DICOM file.")
            return None

        # Get pixel array
        pixel_array = dataset.pixel_array

        # Handle multi-frame images
        if len(pixel_array.shape) > 2:
            total_frames = pixel_array.shape[0]
            print(f"  Multi-frame image detected: {total_frames} frames")
            if frame_number >= total_frames:
                print(f"  Warning: Frame {frame_number} does not exist. Using frame 0.")
                frame_number = 0
            pixel_array = pixel_array[frame_number]
            print(f"  Extracting frame: {frame_number}")

        # Get image information
        rows, cols = pixel_array.shape
        print(f"  Image size: {cols} x {rows}")
        print(f"  Pixel value range: {pixel_array.min()} to {pixel_array.max()}")

        # Get window settings from DICOM tags if not provided
        if window_center is None or window_width is None:
            wc = dataset.get('WindowCenter', None)
            ww = dataset.get('WindowWidth', None)

            if wc is not None and ww is not None:
                # Handle multiple window settings
                if isinstance(wc, pydicom.multival.MultiValue):
                    window_center = int(wc[0])
                    window_width = int(ww[0])
                else:
                    window_center = int(wc)
                    window_width = int(ww)
                print(f"  Using DICOM window settings: C={window_center}, W={window_width}")
            else:
                # Auto-calculate window settings
                window_center, window_width = auto_window(pixel_array)
                print(f"  Auto-calculated window settings: C={window_center}, W={window_width}")

        # Apply windowing
        windowed_image = apply_windowing(pixel_array, window_center, window_width)

        # Handle photometric interpretation
        photometric = dataset.get('PhotometricInterpretation', '')
        if photometric == 'MONOCHROME1':
            # Invert for MONOCHROME1
            windowed_image = 255 - windowed_image
            print(f"  Applied MONOCHROME1 inversion")

        # Create output filename if not provided
        if output_file is None:
            base, _ = os.path.splitext(input_file)
            if frame_number > 0:
                output_file = f"{base}_frame{frame_number}.{output_format}"
            else:
                output_file = f"{base}.{output_format}"

        # Convert to PIL Image and save
        image = Image.fromarray(windowed_image)

        if output_format.lower() == 'jpeg':
            image.save(output_file, 'JPEG', quality=95)
        else:
            image.save(output_file, 'PNG')

        print(f"\n✓ Conversion successful!")
        print(f"  Output file: {output_file}")
        print(f"  Format: {output_format.upper()}")
        print(f"{'='*80}\n")

        return output_file

    except Exception as e:
        print(f"Error converting DICOM file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None

def convert_all_frames(input_file, output_format='png'):
    """Convert all frames from a multi-frame DICOM file."""
    try:
        from PIL import Image
        dataset = pydicom.dcmread(input_file, force=True)

        if 'PixelData' not in dataset:
            print("Error: No pixel data found in DICOM file.")
            return

        pixel_array = dataset.pixel_array

        if len(pixel_array.shape) <= 2:
            print("This is a single-frame image. Use convert_dicom_to_image instead.")
            return

        total_frames = pixel_array.shape[0]
        print(f"\nConverting all {total_frames} frames from: {input_file}")
        print(f"{'='*80}")

        for frame_num in range(total_frames):
            convert_dicom_to_image(input_file, output_format=output_format,
                                 frame_number=frame_num)

        print(f"✓ All {total_frames} frames converted successfully!\n")

    except Exception as e:
        print(f"Error converting frames: {e}", file=sys.stderr)

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_format = sys.argv[2] if len(sys.argv) > 2 else 'png'

        # Check if user wants to convert all frames
        if len(sys.argv) > 3 and sys.argv[3] == '--all-frames':
            convert_all_frames(input_file, output_format)
        else:
            output_file = sys.argv[3] if len(sys.argv) > 3 else None
            convert_dicom_to_image(input_file, output_file, output_format)
    else:
        print("Usage: dicom-to-image <input_file> [output_format] [output_file/--all-frames]")
        if os.path.exists("1.dcm"):
             convert_dicom_to_image("1.dcm", output_format='png')

if __name__ == "__main__":
    main()

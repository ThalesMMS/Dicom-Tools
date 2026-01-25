#!/usr/bin/env python3
#
# pixel_stats.py
# Dicom-Tools-py
#
# Calculates and compares statistical metrics for DICOM pixel data, with optional histograms.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Analyze and display pixel data statistics from DICOM files.
This script provides detailed statistical analysis of pixel values,
including histogram data, intensity ranges, and distribution metrics.
"""

import pydicom
import sys
import os
import argparse
import numpy as np

from .core.images import calculate_statistics

def display_statistics(input_file, frame_number=0, show_histogram=False):
    """
    Display pixel data statistics for a DICOM file.

    Args:
        input_file: Path to DICOM file
        frame_number: Frame number for multi-frame images (0-based)
        show_histogram: Whether to show histogram
    """
    try:
        # Read the DICOM file
        print(f"\nReading DICOM file: {input_file}")
        dataset = pydicom.dcmread(input_file, force=True)

        if 'PixelData' not in dataset:
            print("Error: No pixel data found in DICOM file.")
            return

        # Get pixel array
        pixel_array = dataset.pixel_array
        # Accessing pixel_array triggers decompression; do it once and reuse the result

        print(f"{'='*80}")
        print(f"Pixel Data Statistics")
        print(f"{'='*80}")
        print(f"File: {os.path.basename(input_file)}\n")

        # Handle multi-frame
        if len(pixel_array.shape) > 2:
            total_frames = pixel_array.shape[0]
            print(f"Multi-frame image: {total_frames} frames")
            if frame_number >= total_frames:
                print(f"Warning: Frame {frame_number} does not exist. Using frame 0.")
                frame_number = 0
            print(f"Analyzing frame: {frame_number}\n")
            pixel_array = pixel_array[frame_number]

        # Image dimensions
        if len(pixel_array.shape) == 2:
            rows, cols = pixel_array.shape
            print(f"Image Dimensions: {cols} x {rows}")
        else:
            rows, cols, channels = pixel_array.shape
            print(f"Image Dimensions: {cols} x {rows} x {channels} channels")

        print(f"Data Type: {pixel_array.dtype}")
        print(f"Bits per Pixel: {pixel_array.itemsize * 8}")

        # DICOM metadata
        print(f"\nDICOM Metadata:")
        print(f"  Bits Allocated     : {dataset.get('BitsAllocated', 'N/A')}")
        print(f"  Bits Stored        : {dataset.get('BitsStored', 'N/A')}")
        print(f"  High Bit           : {dataset.get('HighBit', 'N/A')}")
        print(f"  Pixel Representation: {dataset.get('PixelRepresentation', 'N/A')}")
        print(f"  Photometric Interp.: {dataset.get('PhotometricInterpretation', 'N/A')}")

        # Window/Level if available
        if 'WindowCenter' in dataset:
            wc = dataset.WindowCenter
            ww = dataset.WindowWidth
            if isinstance(wc, pydicom.multival.MultiValue):
                wc = wc[0]
                ww = ww[0]
            print(f"  Window Center      : {wc}")
            print(f"  Window Width       : {ww}")

        # Calculate statistics
        print(f"\n{'─'*80}")
        print("PIXEL VALUE STATISTICS")
        print(f"{'─'*80}")

        stats = calculate_statistics(pixel_array)

        print(f"\nBasic Statistics:")
        print(f"  Minimum            : {stats['min']}")
        print(f"  Maximum            : {stats['max']}")
        print(f"  Range              : {stats['range']}")
        print(f"  Mean               : {stats['mean']:.2f}")
        print(f"  Median             : {stats['median']:.2f}")
        print(f"  Std Deviation      : {stats['std']:.2f}")
        print(f"  Variance           : {stats['variance']:.2f}")

        print(f"\nPercentiles:")
        print(f"  1st Percentile     : {stats['p1']:.2f}")
        print(f"  5th Percentile     : {stats['p5']:.2f}")
        print(f"  25th Percentile (Q1): {stats['p25']:.2f}")
        print(f"  50th Percentile (Median): {stats['median']:.2f}")
        print(f"  75th Percentile (Q3): {stats['p75']:.2f}")
        print(f"  95th Percentile    : {stats['p95']:.2f}")
        print(f"  99th Percentile    : {stats['p99']:.2f}")

        print(f"\nDistribution:")
        print(f"  Total Pixels       : {stats['total_pixels']:,}")
        print(f"  Unique Values      : {stats['unique_values']:,}")
        print(f"  Zero Pixels        : {stats['zero_pixels']:,} ({stats['zero_percent']:.2f}%)")
        print(f"  IQR (Q3-Q1)        : {stats['iqr']:.2f}")

        # Histogram
        if show_histogram:
            print(f"\n{'─'*80}")
            print("HISTOGRAM")
            print(f"{'─'*80}")
            display_histogram(pixel_array, bins=20)

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"Error analyzing pixel data: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

def display_histogram(pixel_array, bins=20):
    """
    Display a text-based histogram of pixel values.

    Args:
        pixel_array: NumPy array of pixel data
        bins: Number of histogram bins
    """
    flat_pixels = pixel_array.flatten()

    # Calculate histogram
    hist, bin_edges = np.histogram(flat_pixels, bins=bins)

    # Find max count for scaling
    max_count = np.max(hist)
    bar_width = 50  # Width of the histogram bars

    # Display histogram
    for i in range(len(hist)):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        count = hist[i]

        # Scale bar height relative to the busiest bin so the graph fits the console
        if max_count > 0:
            bar_len = int((count / max_count) * bar_width)
        else:
            bar_len = 0

        bar = '█' * bar_len
        percentage = (count / len(flat_pixels)) * 100

        print(f"  [{bin_start:8.1f} - {bin_end:8.1f}]: {bar:<{bar_width}} {count:8,} ({percentage:5.2f}%)")

def compare_pixel_stats(file1, file2):
    """
    Compare pixel statistics between two DICOM files.

    Args:
        file1: First DICOM file
        file2: Second DICOM file
    """
    try:
        print(f"\n{'='*80}")
        print(f"Pixel Statistics Comparison")
        print(f"{'='*80}\n")

        # Read both files
        ds1 = pydicom.dcmread(file1, force=True)
        ds2 = pydicom.dcmread(file2, force=True)

        if 'PixelData' not in ds1 or 'PixelData' not in ds2:
            print("Error: One or both files do not contain pixel data.")
            return

        # Get pixel arrays
        px1 = ds1.pixel_array
        px2 = ds2.pixel_array

        # Handle multi-frame (use first frame)
        if len(px1.shape) > 2:
            px1 = px1[0]
        if len(px2.shape) > 2:
            px2 = px2[0]

        # Calculate statistics
        stats1 = calculate_statistics(px1)
        stats2 = calculate_statistics(px2)

        # Display comparison
        print(f"{'Statistic':<25} {'File 1':<20} {'File 2':<20} {'Difference'}")
        print(f"{'─'*90}")

        metrics = [
            ('Dimensions', f"{px1.shape[1]}x{px1.shape[0]}", f"{px2.shape[1]}x{px2.shape[0]}", ''),
            ('Minimum', stats1['min'], stats2['min'], stats2['min'] - stats1['min']),
            ('Maximum', stats1['max'], stats2['max'], stats2['max'] - stats1['max']),
            ('Mean', f"{stats1['mean']:.2f}", f"{stats2['mean']:.2f}", f"{stats2['mean'] - stats1['mean']:.2f}"),
            ('Median', f"{stats1['median']:.2f}", f"{stats2['median']:.2f}", f"{stats2['median'] - stats1['median']:.2f}"),
            ('Std Dev', f"{stats1['std']:.2f}", f"{stats2['std']:.2f}", f"{stats2['std'] - stats1['std']:.2f}"),
            ('Range', stats1['range'], stats2['range'], stats2['range'] - stats1['range']),
            ('Total Pixels', f"{stats1['total_pixels']:,}", f"{stats2['total_pixels']:,}", ''),
            ('Unique Values', f"{stats1['unique_values']:,}", f"{stats2['unique_values']:,}", ''),
        ]

        for metric, val1, val2, diff in metrics:
            diff_str = str(diff) if diff != '' else ''
            print(f"{metric:<25} {str(val1):<20} {str(val2):<20} {diff_str}")

        # Check if pixel data is identical
        if px1.shape == px2.shape:
            if np.array_equal(px1, px2):
                print(f"\n✓ Pixel data is IDENTICAL")
            else:
                diff_pixels = np.sum(px1 != px2)
                diff_percent = (diff_pixels / px1.size) * 100
                print(f"\n✗ Pixel data is DIFFERENT")
                print(f"  Different pixels: {diff_pixels:,} ({diff_percent:.2f}%)")

                # Calculate difference metrics
                abs_diff = np.abs(px2.astype(np.int32) - px1.astype(np.int32))
                print(f"  Mean absolute difference: {np.mean(abs_diff):.2f}")
                print(f"  Max absolute difference: {np.max(abs_diff)}")
        else:
            print(f"\n⚠ Images have different dimensions, cannot compare pixel values")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"Error comparing files: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description='Analyze pixel data statistics in DICOM files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Show statistics for a file
  %(prog)s image.dcm

  # Show statistics with histogram
  %(prog)s image.dcm --histogram

  # Analyze specific frame of multi-frame image
  %(prog)s multiframe.dcm --frame 5

  # Compare two files
  %(prog)s file1.dcm --compare file2.dcm
        '''
    )

    parser.add_argument('input_file', help='Input DICOM file')
    parser.add_argument('-f', '--frame', type=int, default=0,
                        help='Frame number for multi-frame images (0-based, default: 0)')
    parser.add_argument('--histogram', action='store_true',
                        help='Display histogram of pixel values')
    parser.add_argument('--bins', type=int, default=20,
                        help='Number of histogram bins (default: 20)')
    parser.add_argument('-c', '--compare', metavar='FILE',
                        help='Compare pixel statistics with another file')

    args = parser.parse_args()

    if args.compare:
        compare_pixel_stats(args.input_file, args.compare)
    else:
        display_statistics(args.input_file, args.frame, args.histogram)

    return 0

if __name__ == "__main__":
    sys.exit(main())

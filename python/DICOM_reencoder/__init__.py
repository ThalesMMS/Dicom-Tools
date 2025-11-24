#
# __init__.py
# Dicom-Tools-py
#
# Exports shared modules and package metadata for the DICOM Tools suite.
#
# Thales Matheus Mendonça Santos - November 2025

"""
DICOM Tools - Comprehensive DICOM utilities for medical imaging.

This package provides a complete set of tools for working with DICOM files,
including inspection, conversion, anonymization, validation, and networking.
"""

__version__ = '1.0.0'
__author__ = 'Thales MMS'
__license__ = 'MIT'

# Import main functions for programmatic use
from . import (
    core,
    extract_metadata,
    dicom_info,
    comparar_dicom,
    reencode_dicom,
    decompress_dicom,
    convert_to_image,
    anonymize_dicom,
    validate_dicom,
    pixel_stats,
    modify_tags,
    organize_dicom,
    search_dicom,
    split_multiframe,
    batch_process,
)

__all__ = [
    'extract_metadata',
    'dicom_info',
    'comparar_dicom',
    'reencode_dicom',
    'decompress_dicom',
    'convert_to_image',
    'anonymize_dicom',
    'validate_dicom',
    'pixel_stats',
    'modify_tags',
    'organize_dicom',
    'search_dicom',
    'split_multiframe',
    'batch_process',
    'core',
]

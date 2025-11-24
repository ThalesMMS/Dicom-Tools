#!/usr/bin/env python3
"""
Setup script for DICOM Tools package.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='dicom-tools',
    version='1.0.0',
    description='Comprehensive DICOM utilities for inspection, conversion, anonymization, and processing',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Thales MMS',
    author_email='',
    url='https://github.com/ThalesMMS/Dicom-Tools',
    license='MIT',

    packages=find_packages(),
    include_package_data=True,

    python_requires='>=3.9',

    install_requires=[
        'pydicom>=2.3.0',
        'numpy>=1.20.0',
        'Pillow>=9.0.0',
        'pynetdicom>=2.0.0',  # For DICOM networking
        'flask>=2.0.0',        # For web interface
        'flask-cors>=3.0.0',   # For CORS support
    ],

    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'gdcm>=3.0.0',
            'SimpleITK>=2.2.0',
            'dicom-numpy>=0.5.0',
        ],
        'web': [
            'flask>=2.0.0',
            'flask-cors>=3.0.0',
        ],
        'networking': [
            'pynetdicom>=2.0.0',
        ],
        'extra': [
            'gdcm>=3.0.0',
            'SimpleITK>=2.2.0',
            'dicom-numpy>=0.5.0',
        ],
    },

    entry_points={
        'console_scripts': [
            # Inspection and Metadata
            'dicom-extract-metadata=DICOM_reencoder.extract_metadata:main',
            'dicom-info=DICOM_reencoder.dicom_info:main',
            'dicom-compare=DICOM_reencoder.comparar_dicom:main',

            # Conversion and Re-encoding
            'dicom-reencode=DICOM_reencoder.reencode_dicom:main',
            'dicom-decompress=DICOM_reencoder.decompress_dicom:main',
            'dicom-to-image=DICOM_reencoder.convert_to_image:main',

            # Privacy and Anonymization
            'dicom-anonymize=DICOM_reencoder.anonymize_dicom:main',

            # Validation and Analysis
            'dicom-validate=DICOM_reencoder.validate_dicom:main',
            'dicom-pixel-stats=DICOM_reencoder.pixel_stats:main',

            # Modification and Organization
            'dicom-modify=DICOM_reencoder.modify_tags:main',
            'dicom-organize=DICOM_reencoder.organize_dicom:main',

            # Search and Filtering
            'dicom-search=DICOM_reencoder.search_dicom:main',

            # Multi-frame
            'dicom-split-multiframe=DICOM_reencoder.split_multiframe:main',

            # Batch Processing
            'dicom-batch=DICOM_reencoder.batch_process:main',

            # Volume utilities
            'dicom-volume=DICOM_reencoder.volume_builder:main',
            'dicom-to-nifti=DICOM_reencoder.series_to_nifti:main',
            'dicom-transcode=DICOM_reencoder.transcode_dicom:main',

            # DICOM Networking
            'dicom-query=DICOM_reencoder.dicom_query:main',
            'dicom-retrieve=DICOM_reencoder.dicom_retrieve:main',
            'dicom-echo=DICOM_reencoder.dicom_echo:main',

            # Web Interface
            'dicom-web=DICOM_reencoder.web_interface:main',
            'dicom-tools=DICOM_reencoder.cli:main',
        ],
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='dicom medical imaging healthcare radiology pydicom anonymization conversion validation',

    project_urls={
        'Bug Reports': 'https://github.com/ThalesMMS/Dicom-Tools/issues',
        'Source': 'https://github.com/ThalesMMS/Dicom-Tools',
        'Documentation': 'https://github.com/ThalesMMS/Dicom-Tools#readme',
    },
)

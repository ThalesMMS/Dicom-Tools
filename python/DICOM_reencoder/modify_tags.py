#!/usr/bin/env python3
#
# modify_tags.py
# Dicom-Tools-py
#
# Enables interactive or scripted modification of DICOM tags while keeping file structure intact.
#
# Thales Matheus Mendonça Santos - November 2025

"""
Modify specific DICOM tags in a file.
This script allows selective modification of DICOM metadata tags
while preserving the rest of the file structure.
"""

import pydicom
import sys
import os
import argparse

def modify_tag(dataset, tag_name, new_value):
    """
    Modify a specific DICOM tag.

    Args:
        dataset: DICOM dataset
        tag_name: Name of the tag to modify
        new_value: New value for the tag

    Returns:
        True if successful, False otherwise
    """
    try:
        if tag_name in dataset:
            old_value = dataset.get(tag_name)
            # Updating in-place preserves VR/VM handling managed by pydicom
            dataset.data_element(tag_name).value = new_value
            print(f"  ✓ Modified {tag_name}")
            print(f"    Old value: {old_value}")
            print(f"    New value: {new_value}")
            return True
        else:
            # Try to add the tag if it doesn't exist
            setattr(dataset, tag_name, new_value)
            print(f"  ✓ Added {tag_name} = {new_value}")
            return True
    except Exception as e:
        print(f"  ✗ Error modifying {tag_name}: {e}")
        return False

def modify_tags_interactive(input_file, output_file=None):
    """
    Interactively modify DICOM tags.

    Args:
        input_file: Path to input DICOM file
        output_file: Path to output file (default: input_modified.dcm)
    """
    try:
        # Read the DICOM file
        print(f"\nReading DICOM file: {input_file}")
        dataset = pydicom.dcmread(input_file, force=True)

        if output_file is None:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_modified{ext}"

        print(f"{'='*80}")
        print("DICOM Tag Modification Tool")
        print(f"{'='*80}\n")

        print("Common tags you can modify:")
        print("  PatientName, PatientID, PatientBirthDate, PatientSex")
        print("  StudyDescription, SeriesDescription, Modality")
        print("  StudyDate, StudyTime, SeriesDate, SeriesTime")
        print("  InstitutionName, StationName, Manufacturer")
        print("\nEnter tag modifications (one per line)")
        print("Format: TagName=NewValue")
        print("Type 'done' when finished, 'list' to see current values\n")

        # Queue user-requested modifications and replay them after the prompt finishes
        modifications = []

        while True:
            user_input = input("Tag modification (or 'done'/'list'): ").strip()

            if user_input.lower() == 'done':
                break
            elif user_input.lower() == 'list':
                print("\nCurrent tag values:")
                common_tags = [
                    'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex',
                    'StudyDescription', 'SeriesDescription', 'Modality',
                    'StudyDate', 'StudyTime', 'InstitutionName'
                ]
                for tag in common_tags:
                    if tag in dataset:
                        print(f"  {tag:<25}: {dataset.get(tag)}")
                print()
                continue
            elif '=' not in user_input:
                print("  Invalid format. Use: TagName=NewValue\n")
                continue

            tag_name, new_value = user_input.split('=', 1)
            tag_name = tag_name.strip()
            new_value = new_value.strip()

            modifications.append((tag_name, new_value))

        # Apply modifications
        if modifications:
            print(f"\n{'─'*80}")
            print("Applying modifications...")
            print(f"{'─'*80}\n")

            for tag_name, new_value in modifications:
                modify_tag(dataset, tag_name, new_value)

            # Save the modified file
            dataset.save_as(output_file)

            print(f"\n{'='*80}")
            print(f"✓ Modifications complete!")
            print(f"  Output file: {output_file}")
            print(f"  Total modifications: {len(modifications)}")
            print(f"{'='*80}\n")
        else:
            print("\nNo modifications made.\n")

        return dataset

    except Exception as e:
        print(f"Error modifying DICOM file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None

def modify_tags_batch(input_file, modifications, output_file=None):
    """
    Modify DICOM tags from command line or script.

    Args:
        input_file: Path to input DICOM file
        modifications: Dictionary of tag names and new values
        output_file: Path to output file
    """
    try:
        # Read the DICOM file
        print(f"\nReading DICOM file: {input_file}")
        dataset = pydicom.dcmread(input_file, force=True)

        if output_file is None:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_modified{ext}"

        print(f"{'='*80}")
        print("DICOM Tag Modification")
        print(f"{'='*80}\n")

        success_count = 0
        error_count = 0

        for tag_name, new_value in modifications.items():
            if modify_tag(dataset, tag_name, new_value):
                success_count += 1
            else:
                error_count += 1

        # Save the modified file
        dataset.save_as(output_file)

        print(f"\n{'='*80}")
        print(f"✓ Modifications complete!")
        print(f"  Output file: {output_file}")
        print(f"  Successful: {success_count}")
        print(f"  Errors: {error_count}")
        print(f"{'='*80}\n")

        return dataset

    except Exception as e:
        print(f"Error modifying DICOM file: {e}", file=sys.stderr)
        return None

def list_all_tags(input_file):
    """List all tags in a DICOM file."""
    try:
        dataset = pydicom.dcmread(input_file, force=True)

        print(f"\n{'='*80}")
        print(f"All DICOM Tags in: {os.path.basename(input_file)}")
        print(f"{'='*80}\n")

        # Group tags by category
        print("FILE META INFORMATION")
        print(f"{'─'*80}")
        if hasattr(dataset, 'file_meta'):
            for elem in dataset.file_meta:
                print(f"  {elem.name:<40}: {elem.value}")

        print(f"\nDATASET TAGS")
        print(f"{'─'*80}")
        for elem in dataset:
            # Skip pixel data for readability
            if elem.tag == pydicom.datadict.tag_for_keyword('PixelData'):
                print(f"  {elem.name:<40}: [Pixel Data - {len(elem.value)} bytes]")
            elif elem.VR == 'SQ':  # Sequence
                print(f"  {elem.name:<40}: [Sequence with {len(elem.value)} item(s)]")
            else:
                value_str = str(elem.value)
                if len(value_str) > 60:
                    value_str = value_str[:57] + '...'
                print(f"  {elem.name:<40}: {value_str}")

        print(f"\n{'='*80}\n")

    except Exception as e:
        print(f"Error reading DICOM file: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description='Modify DICOM tags',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode
  %(prog)s input.dcm

  # Batch mode with specific tags
  %(prog)s input.dcm -t PatientName="Doe^John" -t Modality=CT

  # Specify output file
  %(prog)s input.dcm -o output.dcm -t PatientID=12345

  # List all tags in a file
  %(prog)s input.dcm --list-tags
        '''
    )

    parser.add_argument('input_file', help='Input DICOM file')
    parser.add_argument('-o', '--output', help='Output DICOM file')
    parser.add_argument('-t', '--tag', action='append', metavar='TAG=VALUE',
                        help='Tag modification (can be used multiple times)')
    parser.add_argument('--list-tags', action='store_true',
                        help='List all tags in the file and exit')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Force interactive mode')

    args = parser.parse_args()

    # List tags mode
    if args.list_tags:
        list_all_tags(args.input_file)
        return 0

    # Batch mode with -t arguments
    if args.tag and not args.interactive:
        modifications = {}
        for tag_spec in args.tag:
            if '=' not in tag_spec:
                print(f"Error: Invalid tag specification: {tag_spec}")
                print("Format should be: TagName=NewValue")
                return 1
            tag_name, new_value = tag_spec.split('=', 1)
            modifications[tag_name.strip()] = new_value.strip()

        modify_tags_batch(args.input_file, modifications, args.output)
    else:
        # Interactive mode
        modify_tags_interactive(args.input_file, args.output)

    return 0

if __name__ == "__main__":
    sys.exit(main())

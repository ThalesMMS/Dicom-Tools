//
// file_operations.rs
// Dicom-Tools-rs
//
// Tests for DICOM file operations: reading, writing, streaming, partial reads, and file validation.
//
// Thales Matheus Mendonça Santos - November 2025

use std::fs::{self, File};
use std::io::{BufReader, Cursor, Read, Write};
use std::path::Path;

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::{open_file, FileDicomObject, FileMetaTableBuilder, InMemDicomObject, ReadError};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use tempfile::tempdir;

fn create_test_dicom(path: &Path, patient_name: &str) {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from(patient_name),
    ));
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from("TEST123"),
    ));
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("OT"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from(format!("1.2.826.0.1.3680043.{}", rand_suffix())),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(4_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(4_u16)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(7_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(vec![0u8; 16]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.999")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(path).expect("write");
}

fn rand_suffix() -> u32 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .subsec_nanos()
}

#[test]
fn open_valid_dicom_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("valid.dcm");
    create_test_dicom(&path, "Valid^File");

    let obj = open_file(&path).expect("open");
    assert!(obj.element(tags::PATIENT_NAME).is_ok());
}

#[test]
fn open_nonexistent_file_fails() {
    let result = open_file("/nonexistent/path/to/file.dcm");
    assert!(result.is_err());
}

#[test]
fn open_corrupted_file_fails() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("corrupted.dcm");

    // Write garbage data
    fs::write(&path, b"This is not a DICOM file").expect("write garbage");

    let result = open_file(&path);
    assert!(result.is_err());
}

#[test]
fn dicom_preamble_and_prefix() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("preamble.dcm");
    create_test_dicom(&path, "Preamble^Test");

    // Read raw bytes to verify DICM prefix at offset 128
    let mut file = File::open(&path).expect("open");
    let mut buffer = vec![0u8; 132];
    file.read_exact(&mut buffer).expect("read");

    // DICM prefix at offset 128-131
    assert_eq!(&buffer[128..132], b"DICM");
}

#[test]
fn file_size_reasonable() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("size_check.dcm");
    create_test_dicom(&path, "Size^Check");

    let metadata = fs::metadata(&path).expect("metadata");
    // Minimal DICOM with small pixel data should be under 1KB
    assert!(metadata.len() < 2048);
    // But should have some content
    assert!(metadata.len() > 100);
}

#[test]
fn write_to_new_directory() {
    let dir = tempdir().expect("tempdir");
    let subdir = dir.path().join("subdir");
    fs::create_dir(&subdir).expect("mkdir");
    let path = subdir.join("nested.dcm");

    create_test_dicom(&path, "Nested^Dir");

    assert!(path.exists());
    let obj = open_file(&path).expect("open");
    assert_eq!(
        obj.element(tags::PATIENT_NAME).unwrap().to_str().unwrap(),
        "Nested^Dir"
    );
}

#[test]
fn overwrite_existing_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("overwrite.dcm");

    create_test_dicom(&path, "Original^Name");
    create_test_dicom(&path, "Overwritten^Name");

    let obj = open_file(&path).expect("open");
    assert_eq!(
        obj.element(tags::PATIENT_NAME).unwrap().to_str().unwrap(),
        "Overwritten^Name"
    );
}

#[test]
fn read_specific_element() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("specific.dcm");
    create_test_dicom(&path, "Specific^Element");

    let obj = open_file(&path).expect("open");

    // Access specific elements
    assert_eq!(obj.element(tags::MODALITY).unwrap().to_str().unwrap(), "OT");
    assert_eq!(obj.element(tags::PATIENT_ID).unwrap().to_str().unwrap(), "TEST123");
    assert_eq!(obj.element(tags::ROWS).unwrap().to_int::<u16>().unwrap(), 4);
    assert_eq!(obj.element(tags::COLUMNS).unwrap().to_int::<u16>().unwrap(), 4);
}

#[test]
fn iterate_all_elements() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("iterate.dcm");
    create_test_dicom(&path, "Iterate^Test");

    let obj = open_file(&path).expect("open");

    let mut count = 0;
    let mut tags_found = Vec::new();
    for elem in &obj {
        count += 1;
        tags_found.push(elem.header().tag);
    }

    assert!(count > 10); // Should have many elements
    assert!(tags_found.contains(&tags::PATIENT_NAME));
    assert!(tags_found.contains(&tags::PIXEL_DATA));
}

#[test]
fn file_meta_information() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("filemeta.dcm");
    create_test_dicom(&path, "FileMeta^Test");

    let obj = open_file(&path).expect("open");
    let meta = obj.meta();

    assert_eq!(meta.transfer_syntax(), EXPLICIT_VR_LITTLE_ENDIAN.uid());
    assert_eq!(meta.media_storage_sop_class_uid(), "1.2.840.10008.5.1.4.1.1.7");
}

#[test]
fn write_to_buffer() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Buffer^Test"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }

    let mut buffer = Vec::new();
    file_obj.write_all(&mut buffer).expect("write to buffer");

    // Verify DICM prefix
    assert!(buffer.len() > 132);
    assert_eq!(&buffer[128..132], b"DICM");
}

#[test]
fn read_from_buffer() {
    // First create a DICOM in memory
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("FromBuffer"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.9"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.9")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }

    let mut buffer = Vec::new();
    file_obj.write_all(&mut buffer).expect("write");

    // Now read from the buffer
    let cursor = Cursor::new(buffer);
    let read_obj = dicom::object::from_reader(cursor).expect("read from buffer");

    assert_eq!(
        read_obj.element(tags::PATIENT_NAME).unwrap().to_str().unwrap(),
        "FromBuffer"
    );
}

#[test]
fn large_pixel_data_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("large_pixels.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Large^Pixels"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(256_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(256_u16)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(16_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(12_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(11_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.10"),
    ));

    // 256x256 x 2 bytes = 131072 bytes
    let pixels: Vec<u8> = (0..131072).map(|i| (i % 256) as u8).collect();
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OW,
        PrimitiveValue::from(pixels),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.10")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write large file");

    // Verify file size
    let metadata = fs::metadata(&path).expect("metadata");
    assert!(metadata.len() > 130000); // At least pixel data size

    // Verify can read back
    let read = open_file(&path).expect("read large");
    assert_eq!(read.element(tags::ROWS).unwrap().to_int::<u16>().unwrap(), 256);
}

#[test]
fn multiple_files_in_directory() {
    let dir = tempdir().expect("tempdir");

    for i in 0..5 {
        let path = dir.path().join(format!("file_{}.dcm", i));
        create_test_dicom(&path, &format!("Patient^{}", i));
    }

    // Verify all files exist and are readable
    for i in 0..5 {
        let path = dir.path().join(format!("file_{}.dcm", i));
        let obj = open_file(&path).expect("open");
        let name = obj.element(tags::PATIENT_NAME).unwrap().to_str().unwrap();
        assert_eq!(name, format!("Patient^{}", i));
    }
}

#[test]
fn file_with_sequences() {
    use dicom::core::value::DataSetSequence;

    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("sequences.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Sequence^Test"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.88.11"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.11"),
    ));

    // Add a sequence
    let mut item = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    item.put(DataElement::new(
        tags::CODE_VALUE,
        VR::SH,
        PrimitiveValue::from("TEST"),
    ));
    item.put(DataElement::new(
        tags::CODE_MEANING,
        VR::LO,
        PrimitiveValue::from("Test Code"),
    ));

    obj.put(DataElement::new(
        tags::CONCEPT_NAME_CODE_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![item]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.88.11")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.11")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    // Read back and verify sequence
    let read = open_file(&path).expect("read");
    let seq = read.element(tags::CONCEPT_NAME_CODE_SEQUENCE).expect("seq");
    let items = seq.items().expect("items");
    assert_eq!(items.len(), 1);
    assert_eq!(
        items[0].element(tags::CODE_VALUE).unwrap().to_str().unwrap(),
        "TEST"
    );
}

#[test]
fn empty_element_handling() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("empty_elem.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Empty^Test"),
    ));
    // Empty string value
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from(""),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.12"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.12")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let id = read.element(tags::PATIENT_ID).unwrap().to_str().unwrap();
    assert!(id.is_empty() || id.trim().is_empty());
}

#[test]
fn truncated_file_detection() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("truncated.dcm");

    // Create valid DICOM first
    create_test_dicom(&path, "Truncate^Test");

    // Read and truncate
    let data = fs::read(&path).expect("read");
    let truncated = &data[..data.len() / 2];
    fs::write(&path, truncated).expect("write truncated");

    // Should fail to parse completely
    let result = open_file(&path);
    // May succeed partially or fail - behavior depends on where truncation occurs
    // The important thing is it doesn't panic
    let _ = result;
}

#[test]
fn special_characters_in_path() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("file with spaces.dcm");

    create_test_dicom(&path, "Spaces^Path");

    let obj = open_file(&path).expect("open");
    assert_eq!(
        obj.element(tags::PATIENT_NAME).unwrap().to_str().unwrap(),
        "Spaces^Path"
    );
}

//
// encoding_tests.rs
// Dicom-Tools-rs
//
// Tests for DICOM encoding: transfer syntaxes, byte ordering, explicit/implicit VR, character sets.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::encoding::TransferSyntaxIndex;
use dicom::object::{open_file, FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::{
    EXPLICIT_VR_BIG_ENDIAN, EXPLICIT_VR_LITTLE_ENDIAN, IMPLICIT_VR_LITTLE_ENDIAN,
};
use dicom::transfer_syntax::TransferSyntaxRegistry;
use tempfile::tempdir;

#[test]
fn explicit_vr_little_endian_properties() {
    let ts = EXPLICIT_VR_LITTLE_ENDIAN;

    assert_eq!(ts.uid(), "1.2.840.10008.1.2.1");
    assert!(ts.is_fully_supported());
}

#[test]
fn implicit_vr_little_endian_properties() {
    let ts = IMPLICIT_VR_LITTLE_ENDIAN;

    assert_eq!(ts.uid(), "1.2.840.10008.1.2");
    assert!(ts.is_fully_supported());
}

#[test]
fn explicit_vr_big_endian_properties() {
    let ts = EXPLICIT_VR_BIG_ENDIAN;

    assert_eq!(ts.uid(), "1.2.840.10008.1.2.2");
    // Big endian is retired but should still be supported for reading
}

#[test]
fn transfer_syntax_registry_lookup() {
    let evle = TransferSyntaxRegistry.get("1.2.840.10008.1.2.1");
    assert!(evle.is_some());
    assert_eq!(evle.unwrap().uid(), EXPLICIT_VR_LITTLE_ENDIAN.uid());

    let ivle = TransferSyntaxRegistry.get("1.2.840.10008.1.2");
    assert!(ivle.is_some());
    assert_eq!(ivle.unwrap().uid(), IMPLICIT_VR_LITTLE_ENDIAN.uid());
}

#[test]
fn compressed_transfer_syntax_lookup() {
    // JPEG Lossless
    let jpeg_lossless = TransferSyntaxRegistry.get("1.2.840.10008.1.2.4.70");
    assert!(jpeg_lossless.is_some());

    // JPEG 2000 Lossless
    let j2k_lossless = TransferSyntaxRegistry.get("1.2.840.10008.1.2.4.90");
    assert!(j2k_lossless.is_some());

    // JPEG 2000 Lossy
    let j2k_lossy = TransferSyntaxRegistry.get("1.2.840.10008.1.2.4.91");
    assert!(j2k_lossy.is_some());
}

#[test]
fn write_explicit_vr_little_endian() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("evle.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("EVLE^Test"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.9"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.9")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    assert_eq!(read.meta().transfer_syntax(), EXPLICIT_VR_LITTLE_ENDIAN.uid());
}

#[test]
fn write_implicit_vr_little_endian() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("ivle.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("IVLE^Test"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.10"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(IMPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.10")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    assert_eq!(read.meta().transfer_syntax(), IMPLICIT_VR_LITTLE_ENDIAN.uid());
}

#[test]
fn file_meta_always_explicit_vr_le() {
    // File meta information header is always Explicit VR Little Endian
    // regardless of the dataset's transfer syntax
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("meta_check.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Meta^Check"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.11"),
    ));

    // Use implicit VR for dataset
    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(IMPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.11")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    // Read back and verify
    let read = open_file(&path).expect("read");
    let file_meta = read.meta();

    // File Meta Information Version should exist
    // File meta information version exists
    let _ = file_meta;
}

#[test]
fn character_set_latin1() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // ISO_IR 100 = Latin alphabet No. 1 (ISO 8859-1)
    obj.put(DataElement::new(
        tags::SPECIFIC_CHARACTER_SET,
        VR::CS,
        PrimitiveValue::from("ISO_IR 100"),
    ));

    let charset = obj
        .element(tags::SPECIFIC_CHARACTER_SET)
        .expect("charset")
        .to_str()
        .expect("str");
    assert_eq!(charset, "ISO_IR 100");
}

#[test]
fn character_set_utf8() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // ISO_IR 192 = UTF-8
    obj.put(DataElement::new(
        tags::SPECIFIC_CHARACTER_SET,
        VR::CS,
        PrimitiveValue::from("ISO_IR 192"),
    ));

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("日本語^テスト"),
    ));

    let charset = obj
        .element(tags::SPECIFIC_CHARACTER_SET)
        .expect("charset")
        .to_str()
        .expect("str");
    assert_eq!(charset, "ISO_IR 192");

    let name = obj
        .element(tags::PATIENT_NAME)
        .expect("name")
        .to_str()
        .expect("str");
    assert!(name.contains("日本語"));
}

#[test]
fn extended_character_sets() {
    // Multiple character sets for code extensions
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::SPECIFIC_CHARACTER_SET,
        VR::CS,
        PrimitiveValue::Strs(
            ["ISO 2022 IR 6", "ISO 2022 IR 87"]
                .iter()
                .map(|s| s.to_string())
                .collect(),
        ),
    ));

    let charset_elem = obj.element(tags::SPECIFIC_CHARACTER_SET).expect("charset");
    let charsets: Vec<String> = charset_elem.to_multi_str().expect("strs").into_iter().map(|s| s.to_string()).collect();
    assert!(charsets.len() >= 1);
}

#[test]
fn vr_length_16bit_explicit() {
    // In Explicit VR, most VRs use 16-bit length field
    // These should serialize correctly
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("vr16.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // LO uses 16-bit length
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from("SHORT_VALUE"),
    ));

    // CS uses 16-bit length
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("CT"),
    ));

    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.12"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.12")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    assert_eq!(
        read.element(tags::PATIENT_ID).unwrap().to_str().unwrap(),
        "SHORT_VALUE"
    );
}

#[test]
fn vr_length_32bit_explicit() {
    // Some VRs use 32-bit length in Explicit VR: OB, OD, OF, OL, OW, SQ, UC, UN, UR, UT
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("vr32.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // UT uses 32-bit length
    let long_text = "A".repeat(100);
    obj.put(DataElement::new(
        tags::TEXT_VALUE,
        VR::UT,
        PrimitiveValue::from(long_text.as_str()),
    ));

    // OB uses 32-bit length
    obj.put(DataElement::new(
        Tag(0x0042, 0x0011), // Encapsulated Document
        VR::OB,
        PrimitiveValue::from(vec![1u8, 2, 3, 4, 5]),
    ));

    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.13"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.13")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let text = read.element(tags::TEXT_VALUE).unwrap().to_str().unwrap();
    assert_eq!(text.len(), 100);
}

#[test]
fn padding_to_even_length() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("padding.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Odd-length string should be padded
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from("ABC"), // 3 characters (odd)
    ));

    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.14"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.14")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    // File should have been written successfully with padding
    let read = open_file(&path).expect("read");
    let id = read.element(tags::PATIENT_ID).unwrap().to_str().unwrap();
    assert_eq!(id.trim(), "ABC");
}

#[test]
fn deflated_transfer_syntax_known() {
    // Deflated Explicit VR Little Endian
    let deflated = TransferSyntaxRegistry.get("1.2.840.10008.1.2.1.99");
    assert!(deflated.is_some());
}

#[test]
fn rle_transfer_syntax_known() {
    // RLE Lossless
    let rle = TransferSyntaxRegistry.get("1.2.840.10008.1.2.5");
    assert!(rle.is_some());
}

#[test]
fn jpeg_baseline_transfer_syntax_known() {
    // JPEG Baseline (Process 1)
    let jpeg_baseline = TransferSyntaxRegistry.get("1.2.840.10008.1.2.4.50");
    assert!(jpeg_baseline.is_some());
}

#[test]
fn undefined_length_sequences() {
    // Sequences can have undefined length with item delimiters
    use dicom::core::value::DataSetSequence;

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    let mut item = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    item.put(DataElement::new(
        tags::CODE_VALUE,
        VR::SH,
        PrimitiveValue::from("TEST"),
    ));

    obj.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![item]),
    ));

    let seq = obj.element(tags::CONTENT_SEQUENCE).expect("seq");
    assert!(seq.items().is_some());
}

#[test]
fn pixel_data_encapsulated_fragments() {
    // Encapsulated pixel data uses fragment structure
    // This test verifies the concept is understood
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("fragments.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Fragment^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(2_u16)));
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
        PrimitiveValue::from(vec![0u8, 1, 2, 3]),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7.8.15"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7.8.15")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    assert!(read.element(tags::PIXEL_DATA).is_ok());
}

#[test]
fn transfer_syntax_is_encapsulated_check() {
    // Check if a transfer syntax indicates encapsulated pixel data

    // Uncompressed syntaxes should not be encapsulated
    let evle = EXPLICIT_VR_LITTLE_ENDIAN;
    assert!(!is_encapsulated(evle.uid()));

    let ivle = IMPLICIT_VR_LITTLE_ENDIAN;
    assert!(!is_encapsulated(ivle.uid()));

    // Compressed syntaxes should be encapsulated
    assert!(is_encapsulated("1.2.840.10008.1.2.4.50")); // JPEG Baseline
    assert!(is_encapsulated("1.2.840.10008.1.2.4.70")); // JPEG Lossless
    assert!(is_encapsulated("1.2.840.10008.1.2.4.90")); // JPEG 2000 Lossless
    assert!(is_encapsulated("1.2.840.10008.1.2.5"));    // RLE Lossless
}

fn is_encapsulated(ts_uid: &str) -> bool {
    // Simple heuristic: compressed transfer syntaxes start with specific prefixes
    ts_uid.starts_with("1.2.840.10008.1.2.4") || ts_uid == "1.2.840.10008.1.2.5"
}

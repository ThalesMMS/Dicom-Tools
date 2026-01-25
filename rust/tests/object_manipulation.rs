//
// object_manipulation.rs
// Dicom-Tools-rs
//
// Tests for DICOM object creation, modification, element access, sequences, and cloning.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::value::DataSetSequence;
use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::mem::InMemDicomObject;
use dicom::object::{FileDicomObject, FileMetaTableBuilder};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use tempfile::tempdir;

#[test]
fn create_empty_object() {
    let obj = InMemDicomObject::new_empty();
    assert_eq!(obj.into_iter().count(), 0);
}

#[test]
fn create_object_with_standard_dictionary() {
    let obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    assert_eq!(obj.into_iter().count(), 0);
}

#[test]
fn put_and_get_string_element() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Doe^John"),
    ));

    let elem = obj.element(tags::PATIENT_NAME).expect("element exists");
    let value = elem.to_str().expect("string value");
    assert_eq!(value, "Doe^John");
}

#[test]
fn put_and_get_numeric_element() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::ROWS,
        VR::US,
        PrimitiveValue::from(512_u16),
    ));

    let elem = obj.element(tags::ROWS).expect("rows");
    let value = elem.to_int::<u16>().expect("u16 value");
    assert_eq!(value, 512);
}

#[test]
fn put_and_get_multiple_numeric_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Pixel spacing has VM 2
    obj.put(DataElement::new(
        tags::PIXEL_SPACING,
        VR::DS,
        PrimitiveValue::from([0.5_f64, 0.5_f64]),
    ));

    let elem = obj.element(tags::PIXEL_SPACING).expect("pixel spacing");
    let values: Vec<f64> = elem.to_multi_float64().expect("f64 values");
    assert_eq!(values.len(), 2);
    assert!((values[0] - 0.5).abs() < 1e-6);
    assert!((values[1] - 0.5).abs() < 1e-6);
}

#[test]
fn overwrite_element_value() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Original^Name"),
    ));

    // Overwrite with new value
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("New^Name"),
    ));

    let elem = obj.element(tags::PATIENT_NAME).expect("element");
    assert_eq!(elem.to_str().expect("str"), "New^Name");
}

#[test]
fn remove_element() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("ToRemove"),
    ));

    assert!(obj.element(tags::PATIENT_NAME).is_ok());

    obj.remove_element(tags::PATIENT_NAME);

    assert!(obj.element(tags::PATIENT_NAME).is_err());
}

#[test]
fn element_count_and_iteration() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Test^Patient"),
    ));
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from("12345"),
    ));
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("CT"),
    ));

    let count = obj.into_iter().count();
    assert_eq!(count, 3);
}

#[test]
fn iterate_elements_in_tag_order() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Insert in non-sorted order
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Test"),
    ));
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("CT"),
    ));
    obj.put(DataElement::new(
        tags::STUDY_DATE,
        VR::DA,
        PrimitiveValue::from("20240101"),
    ));

    let tags: Vec<Tag> = obj.into_iter().map(|e| e.header().tag).collect();

    // Should be in ascending tag order
    for i in 1..tags.len() {
        assert!(tags[i - 1] < tags[i]);
    }
}

#[test]
fn create_nested_sequence() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Create sequence item
    let mut item = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    item.put(DataElement::new(
        tags::CODE_VALUE,
        VR::SH,
        PrimitiveValue::from("ABC123"),
    ));
    item.put(DataElement::new(
        tags::CODE_MEANING,
        VR::LO,
        PrimitiveValue::from("Test Code"),
    ));

    // Add sequence to main object
    obj.put(DataElement::new(
        tags::CONCEPT_NAME_CODE_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![item]),
    ));

    let seq_elem = obj.element(tags::CONCEPT_NAME_CODE_SEQUENCE).expect("sequence");
    let items = seq_elem.items().expect("sequence items");
    assert_eq!(items.len(), 1);

    let first_item = &items[0];
    let code_val = first_item.element(tags::CODE_VALUE).expect("code value");
    assert_eq!(code_val.to_str().expect("str"), "ABC123");
}

#[test]
fn sequence_with_multiple_items() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    let mut items = Vec::new();
    for i in 0..3 {
        let mut item = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        item.put(DataElement::new(
            tags::CODE_VALUE,
            VR::SH,
            PrimitiveValue::from(format!("CODE{}", i)),
        ));
        items.push(item);
    }

    obj.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(items),
    ));

    let seq_elem = obj.element(tags::CONTENT_SEQUENCE).expect("sequence");
    let seq_items = seq_elem.items().expect("items");
    assert_eq!(seq_items.len(), 3);

    for (i, item) in seq_items.iter().enumerate() {
        let code = item.element(tags::CODE_VALUE).expect("code");
        assert_eq!(code.to_str().expect("str"), format!("CODE{}", i));
    }
}

#[test]
fn deeply_nested_sequences() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Level 3 (deepest)
    let mut level3 = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    level3.put(DataElement::new(
        tags::TEXT_VALUE,
        VR::UT,
        PrimitiveValue::from("Deep Value"),
    ));

    // Level 2
    let mut level2 = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    level2.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![level3]),
    ));

    // Level 1
    let mut level1 = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    level1.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![level2]),
    ));

    obj.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![level1]),
    ));

    // Navigate down
    let items1 = obj
        .element(tags::CONTENT_SEQUENCE)
        .expect("l1")
        .items()
        .expect("items1");
    let items2 = items1[0]
        .element(tags::CONTENT_SEQUENCE)
        .expect("l2")
        .items()
        .expect("items2");
    let items3 = items2[0]
        .element(tags::CONTENT_SEQUENCE)
        .expect("l3")
        .items()
        .expect("items3");
    let text = items3[0]
        .element(tags::TEXT_VALUE)
        .expect("text")
        .to_str()
        .expect("str");

    assert_eq!(text, "Deep Value");
}

#[test]
fn binary_data_element() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    let pixels: Vec<u8> = vec![0, 64, 128, 192, 255];
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(pixels.clone()),
    ));

    let elem = obj.element(tags::PIXEL_DATA).expect("pixel data");
    let bytes = elem.to_bytes().expect("bytes");
    assert_eq!(bytes.as_ref(), &pixels[..]);
}

#[test]
fn date_and_time_elements() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::STUDY_DATE,
        VR::DA,
        PrimitiveValue::from("20241130"),
    ));
    obj.put(DataElement::new(
        tags::STUDY_TIME,
        VR::TM,
        PrimitiveValue::from("143052"),
    ));

    let date = obj
        .element(tags::STUDY_DATE)
        .expect("date")
        .to_str()
        .expect("str");
    assert_eq!(date, "20241130");

    let time = obj
        .element(tags::STUDY_TIME)
        .expect("time")
        .to_str()
        .expect("str");
    assert_eq!(time, "143052");
}

#[test]
fn uid_element() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7.1.2.3"),
    ));

    let uid = obj
        .element(tags::SOP_INSTANCE_UID)
        .expect("uid")
        .to_str()
        .expect("str");
    assert!(uid.starts_with("1.2.840"));
}

#[test]
fn write_and_read_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("test.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("WriteRead^Test"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.999"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.999")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    // Read back
    let read_obj = dicom::object::open_file(&path).expect("open");
    let name = read_obj
        .element(tags::PATIENT_NAME)
        .expect("name")
        .to_str()
        .expect("str");
    assert_eq!(name, "WriteRead^Test");
}

#[test]
fn file_meta_information_access() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("meta_test.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Meta^Test"),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.888")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read_obj = dicom::object::open_file(&path).expect("open");
    let file_meta = read_obj.meta();

    assert_eq!(
        file_meta.transfer_syntax(),
        EXPLICIT_VR_LITTLE_ENDIAN.uid()
    );
    assert_eq!(
        file_meta.media_storage_sop_class_uid(),
        "1.2.840.10008.5.1.4.1.1.7"
    );
}

#[test]
fn empty_sequence() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::empty(),
    ));

    let seq_elem = obj.element(tags::CONTENT_SEQUENCE).expect("seq");
    let items = seq_elem.items().expect("items");
    assert!(items.is_empty());
}

#[test]
fn element_vr_preservation() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("VR^Test"),
    ));

    let elem = obj.element(tags::PATIENT_NAME).expect("elem");
    assert_eq!(elem.vr(), VR::PN);
}

#[test]
fn tag_exists_check() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Exists"),
    ));

    assert!(obj.element(tags::PATIENT_NAME).is_ok());
    assert!(obj.element(tags::PATIENT_ID).is_err());
}

#[test]
fn multiple_string_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // ImageType can have multiple values
    obj.put(DataElement::new(
        tags::IMAGE_TYPE,
        VR::CS,
        PrimitiveValue::Strs(
            ["ORIGINAL", "PRIMARY", "AXIAL"]
                .iter()
                .map(|s| s.to_string())
                .collect(),
        ),
    ));

    let elem = obj.element(tags::IMAGE_TYPE).expect("image type");
    let values: Vec<String> = elem.to_multi_str().expect("multi str").into_iter().map(|s| s.to_string()).collect();
    assert_eq!(values.len(), 3);
    assert_eq!(values[0], "ORIGINAL");
    assert_eq!(values[1], "PRIMARY");
    assert_eq!(values[2], "AXIAL");
}

#[test]
fn signed_integer_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // SmallestImagePixelValue can be signed
    obj.put(DataElement::new(
        Tag(0x0028, 0x0106), // Smallest Image Pixel Value
        VR::SS,
        PrimitiveValue::from(-1024_i16),
    ));

    let elem = obj.element(Tag(0x0028, 0x0106)).expect("smallest");
    let value = elem.to_int::<i16>().expect("i16");
    assert_eq!(value, -1024);
}

#[test]
fn float_precision() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::SLICE_THICKNESS,
        VR::DS,
        PrimitiveValue::from([2.5_f64]),
    ));

    let elem = obj.element(tags::SLICE_THICKNESS).expect("thickness");
    let value = elem.to_float64().expect("f64");
    assert!((value - 2.5).abs() < 1e-9);
}

//
// dicom_access_tests.rs
// Dicom-Tools-rs
//
// Testes para o trait ElementAccess que fornece acesso uniforme a elementos DICOM.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom_tools::dicom_access::ElementAccess;
use tempfile::tempdir;

fn create_test_object() -> InMemDicomObject<StandardDataDictionary> {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        Tag(0x0010, 0x0010),
        VR::PN,
        PrimitiveValue::from("Access^Test"),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0010),
        VR::US,
        PrimitiveValue::from(256_u16),
    ));
    obj
}

#[test]
fn test_element_str_inmem() {
    let obj = create_test_object();
    assert_eq!(
        obj.element_str(Tag(0x0010, 0x0010)),
        Some("Access^Test".to_string())
    );
    assert_eq!(obj.element_str(Tag(0x9999, 0x9999)), None);
}

#[test]
fn test_element_u32_inmem() {
    let obj = create_test_object();
    assert_eq!(obj.element_u32(Tag(0x0028, 0x0010)), Some(256));
    assert_eq!(obj.element_u32(Tag(0x9999, 0x9999)), None);
}

#[test]
fn test_has_element_inmem() {
    let obj = create_test_object();
    assert!(obj.has_element(Tag(0x0010, 0x0010)));
    assert!(!obj.has_element(Tag(0x9999, 0x9999)));
}

#[test]
fn test_transfer_syntax_inmem() {
    let obj = create_test_object();
    // InMemDicomObject não tem transfer syntax por padrão
    assert_eq!(obj.transfer_syntax(), None);
}

#[test]
fn test_element_str_filedicom() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("test.dcm");

    let obj = create_test_object();
    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5")
        .build()
        .expect("meta");

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write dicom");

    let file_obj = dicom::object::open_file(&path).expect("open file");
    assert_eq!(
        file_obj.element_str(Tag(0x0010, 0x0010)),
        Some("Access^Test".to_string())
    );
}

#[test]
fn test_element_u32_filedicom() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("test.dcm");

    let obj = create_test_object();
    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5")
        .build()
        .expect("meta");

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write dicom");

    let file_obj = dicom::object::open_file(&path).expect("open file");
    assert_eq!(file_obj.element_u32(Tag(0x0028, 0x0010)), Some(256));
}

#[test]
fn test_transfer_syntax_filedicom() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("test.dcm");

    let obj = create_test_object();
    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5")
        .build()
        .expect("meta");

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write dicom");

    let file_obj = dicom::object::open_file(&path).expect("open file");
    let ts = file_obj.transfer_syntax();
    assert!(ts.is_some());
    assert!(ts.unwrap().contains("1.2.840.10008.1.2.1"));
}


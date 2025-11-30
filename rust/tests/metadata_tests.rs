//
// metadata_tests.rs
// Dicom-Tools-rs
//
// Testes para extração de metadados básicos e detalhados de objetos DICOM.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom_tools::metadata;
use tempfile::tempdir;

fn create_test_object() -> InMemDicomObject<StandardDataDictionary> {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        Tag(0x0010, 0x0010),
        VR::PN,
        PrimitiveValue::from("Test^Patient"),
    ));
    obj.put(DataElement::new(
        Tag(0x0010, 0x0020),
        VR::LO,
        PrimitiveValue::from("PAT123"),
    ));
    obj.put(DataElement::new(
        Tag(0x0010, 0x0030),
        VR::DA,
        PrimitiveValue::from("19900101"),
    ));
    obj.put(DataElement::new(
        Tag(0x0010, 0x0040),
        VR::CS,
        PrimitiveValue::from("M"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0020),
        VR::DA,
        PrimitiveValue::from("20240101"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0030),
        VR::TM,
        PrimitiveValue::from("120000"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0050),
        VR::SH,
        PrimitiveValue::from("ACC456"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0060),
        VR::CS,
        PrimitiveValue::from("CT"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0016),
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.2"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0018),
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6.7"),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0010),
        VR::US,
        PrimitiveValue::from(512_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0011),
        VR::US,
        PrimitiveValue::from(512_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0008),
        VR::IS,
        PrimitiveValue::from("10"),
    ));
    obj
}

#[test]
fn test_extract_basic_metadata() {
    let obj = create_test_object();
    let basic = metadata::extract_basic_metadata(&obj);

    assert_eq!(basic.patient_name, Some("Test^Patient".to_string()));
    assert_eq!(basic.patient_id, Some("PAT123".to_string()));
    assert_eq!(basic.study_date, Some("20240101".to_string()));
    assert_eq!(basic.modality, Some("CT".to_string()));
    assert_eq!(basic.sop_class_uid, Some("1.2.840.10008.5.1.4.1.1.2".to_string()));
    assert_eq!(basic.rows, Some(512));
    assert_eq!(basic.columns, Some(512));
    assert_eq!(basic.number_of_frames, Some(10));
    assert!(!basic.has_pixel_data);
}

#[test]
fn test_extract_detailed_metadata() {
    let obj = create_test_object();
    let detailed = metadata::extract_detailed_metadata(&obj);

    assert_eq!(detailed.patient.get("Name"), Some(&"Test^Patient".to_string()));
    assert_eq!(detailed.patient.get("ID"), Some(&"PAT123".to_string()));
    assert_eq!(detailed.patient.get("Birth Date"), Some(&"19900101".to_string()));
    assert_eq!(detailed.patient.get("Sex"), Some(&"M".to_string()));

    assert_eq!(detailed.study.get("Date"), Some(&"20240101".to_string()));
    assert_eq!(detailed.study.get("Time"), Some(&"120000".to_string()));
    assert_eq!(detailed.study.get("Accession Number"), Some(&"ACC456".to_string()));

    assert_eq!(detailed.image.get("Modality"), Some(&"CT".to_string()));
    assert_eq!(detailed.image.get("Rows"), Some(&"512".to_string()));
    assert_eq!(detailed.image.get("Columns"), Some(&"512".to_string()));
    assert_eq!(detailed.image.get("Number of Frames"), Some(&"10".to_string()));

    assert_eq!(
        detailed.misc.get("SOP Class UID"),
        Some(&"1.2.840.10008.5.1.4.1.1.2".to_string())
    );
    assert_eq!(
        detailed.misc.get("SOP Instance UID"),
        Some(&"1.2.3.4.5.6.7".to_string())
    );
}

#[test]
fn test_extract_metadata_with_pixel_data() {
    let mut obj = create_test_object();
    obj.put(DataElement::new(
        Tag(0x7FE0, 0x0010),
        VR::OB,
        PrimitiveValue::from(vec![0_u8, 1, 2, 3]),
    ));

    let basic = metadata::extract_basic_metadata(&obj);
    assert!(basic.has_pixel_data);
}

#[test]
fn test_extract_metadata_missing_fields() {
    let obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    let basic = metadata::extract_basic_metadata(&obj);

    assert_eq!(basic.patient_name, None);
    assert_eq!(basic.patient_id, None);
    assert_eq!(basic.study_date, None);
    assert_eq!(basic.modality, None);
    assert!(!basic.has_pixel_data);
}

#[test]
fn test_info_report_from_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("test.dcm");

    let obj = create_test_object();
    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.2")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7")
        .build()
        .expect("meta");

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write dicom");

    let report = metadata::info_report(&path).expect("info report");
    assert_eq!(report.basic.patient_name, Some("Test^Patient".to_string()));
    assert_eq!(report.basic.modality, Some("CT".to_string()));
}

#[test]
fn test_info_to_json() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("test.dcm");

    let obj = create_test_object();
    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.2")
        .media_storage_sop_instance_uid("1.2.3.4.5.6.7")
        .build()
        .expect("meta");

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write dicom");

    let json = metadata::info_to_json(&path).expect("json");
    assert!(json.contains("Test^Patient"));
    assert!(json.contains("CT"));
}


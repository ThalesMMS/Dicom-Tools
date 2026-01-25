//
// transcode_tests.rs
// Dicom-Tools-rs
//
// Testes para transcodificação de arquivos DICOM entre transfer syntaxes.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom_tools::transcode::UncompressedTransferSyntax;
use dicom_tools::transcode;
use tempfile::tempdir;

fn create_test_dicom_with_pixels(path: &std::path::Path) {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        Tag(0x0010, 0x0010),
        VR::PN,
        PrimitiveValue::from("Transcode^Test"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0016),
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0018),
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5.6"),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0010),
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0011),
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0002),
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0100),
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0101),
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0102),
        VR::US,
        PrimitiveValue::from(7_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0103),
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0004),
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        Tag(0x7FE0, 0x0010),
        VR::OB,
        PrimitiveValue::from(vec![0_u8, 10, 20, 30]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.3.4.5.6")
        .build()
        .expect("meta");

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(path).expect("write dicom");
}

#[test]
fn test_transcode_to_explicit_vr() {
    let dir = tempdir().expect("tempdir");
    let input_path = dir.path().join("input.dcm");
    let output_path = dir.path().join("output.dcm");

    create_test_dicom_with_pixels(&input_path);

    transcode::transcode(
        &input_path,
        &output_path,
        UncompressedTransferSyntax::ExplicitVRLittleEndian,
    )
    .expect("transcode");

    // Verificar que o arquivo foi criado
    assert!(output_path.exists());

    // Verificar que pode ser lido
    let obj = dicom::object::open_file(&output_path).expect("open transcoded file");
    let patient_name = obj.element(Tag(0x0010, 0x0010)).unwrap().to_str().unwrap();
    assert_eq!(patient_name, "Transcode^Test");
}

#[test]
fn test_transcode_to_implicit_vr() {
    let dir = tempdir().expect("tempdir");
    let input_path = dir.path().join("input.dcm");
    let output_path = dir.path().join("output.dcm");

    create_test_dicom_with_pixels(&input_path);

    transcode::transcode(
        &input_path,
        &output_path,
        UncompressedTransferSyntax::ImplicitVRLittleEndian,
    )
    .expect("transcode");

    // Verificar que o arquivo foi criado
    assert!(output_path.exists());

    // Verificar que pode ser lido
    let obj = dicom::object::open_file(&output_path).expect("open transcoded file");
    let patient_name = obj.element(Tag(0x0010, 0x0010)).unwrap().to_str().unwrap();
    assert_eq!(patient_name, "Transcode^Test");
}

#[test]
fn test_transcode_preserves_metadata() {
    let dir = tempdir().expect("tempdir");
    let input_path = dir.path().join("input.dcm");
    let output_path = dir.path().join("output.dcm");

    create_test_dicom_with_pixels(&input_path);

    transcode::transcode(
        &input_path,
        &output_path,
        UncompressedTransferSyntax::ExplicitVRLittleEndian,
    )
    .expect("transcode");

    let input_obj = dicom::object::open_file(&input_path).expect("open input");
    let output_obj = dicom::object::open_file(&output_path).expect("open output");

    // Verificar que metadados importantes são preservados
    let input_sop = input_obj.element(Tag(0x0008, 0x0018)).unwrap().to_str().unwrap();
    let output_sop = output_obj.element(Tag(0x0008, 0x0018)).unwrap().to_str().unwrap();
    assert_eq!(input_sop, output_sop);
}


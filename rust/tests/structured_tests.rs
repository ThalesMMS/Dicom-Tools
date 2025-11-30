//
// structured_tests.rs
// Dicom-Tools-rs
//
// Testes para navegação em estruturas DICOM aninhadas (SR Content Sequences).
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::Tag;
use dicom::dictionary_std::tags;
use dicom_tools::structured::{PathSegment, value_at_path};

mod support;
use support::build_sr_like_dicom;

#[test]
fn test_value_at_path_simple_element() {
    let (_dir, path) = support::build_sr_like_dicom();
    let obj = dicom::object::open_file(&path).expect("open file");

    let path = vec![PathSegment::element(tags::PATIENT_NAME)];
    let value = value_at_path(&obj, &path);
    assert_eq!(value, Some("Structured^Report".to_string()));
}

#[test]
fn test_value_at_path_sequence_navigation() {
    let (_dir, path) = support::build_sr_like_dicom();
    let obj = dicom::object::open_file(&path).expect("open file");

    // Navegar para ContentSequence -> primeiro item -> ConceptNameCodeSequence -> primeiro item -> CodeMeaning
    let path = vec![
        PathSegment::element(tags::CONTENT_SEQUENCE),
        PathSegment::element(tags::CONCEPT_NAME_CODE_SEQUENCE),
        PathSegment::element(tags::CODE_MEANING),
    ];
    let value = value_at_path(&obj, &path);
    assert_eq!(value, Some("Findings".to_string()));
}

#[test]
fn test_value_at_path_nested_content_sequence() {
    let (_dir, path) = support::build_sr_like_dicom();
    let obj = dicom::object::open_file(&path).expect("open file");

    // Navegar para ContentSequence -> primeiro item -> ContentSequence -> primeiro item -> TextValue
    let path = vec![
        PathSegment::element(tags::CONTENT_SEQUENCE),
        PathSegment::element(tags::CONTENT_SEQUENCE),
        PathSegment::element(tags::TEXT_VALUE),
    ];
    let value = value_at_path(&obj, &path);
    assert_eq!(value, Some("Lesion size 3mm".to_string()));
}

#[test]
fn test_value_at_path_from_file() {
    let (_dir, path) = support::build_sr_like_dicom();

    let segments = vec![PathSegment::element(tags::PATIENT_ID)];
    let value = dicom_tools::structured::value_at_path_from_file(&path, &segments)
        .expect("value from file");
    assert_eq!(value, Some("SR001".to_string()));
}

#[test]
fn test_value_at_path_invalid_path() {
    let (_dir, path) = support::build_sr_like_dicom();
    let obj = dicom::object::open_file(&path).expect("open file");

    // Tentar navegar para um elemento que não existe
    let path = vec![PathSegment::element(Tag(0x9999, 0x9999))];
    let value = value_at_path(&obj, &path);
    assert_eq!(value, None);
}

#[test]
fn test_value_at_path_empty_path() {
    let (_dir, path) = support::build_sr_like_dicom();
    let obj = dicom::object::open_file(&path).expect("open file");

    let path = vec![];
    let value = value_at_path(&obj, &path);
    assert_eq!(value, None);
}

#[test]
fn test_path_segment_element() {
    let segment = PathSegment::element(tags::PATIENT_NAME);
    assert_eq!(segment.tag, tags::PATIENT_NAME);
    assert_eq!(segment.item_index, None);
}

#[test]
fn test_path_segment_item() {
    let segment = PathSegment::item(tags::CONTENT_SEQUENCE, 0);
    assert_eq!(segment.tag, tags::CONTENT_SEQUENCE);
    assert_eq!(segment.item_index, Some(0));
}


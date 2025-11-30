//
// stats_tests.rs
// Dicom-Tools-rs
//
// Testes para cálculo de estatísticas de pixels DICOM.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom_tools::stats;
use tempfile::tempdir;

fn create_test_dicom_with_pixels(path: &std::path::Path, pixels: Vec<u8>) {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        Tag(0x0010, 0x0010),
        VR::PN,
        PrimitiveValue::from("Stats^Test"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0016),
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0018),
        VR::UI,
        PrimitiveValue::from("1.2.3.4.5"),
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
        PrimitiveValue::from(pixels),
    ));

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
    file_obj.write_to_file(path).expect("write dicom");
}

#[test]
fn test_pixel_statistics_basic() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("stats.dcm");

    // Criar imagem 2x2 com valores conhecidos
    let pixels = vec![0_u8, 50, 100, 150];
    create_test_dicom_with_pixels(&path, pixels);

    let stats_result = stats::pixel_statistics_for_file(&path).expect("stats");

    assert_eq!(stats_result.total_pixels, 4);
    assert_eq!(stats_result.shape, vec![1, 1, 2, 2]); // frames, samples, rows, cols
    assert!(stats_result.min >= 0.0);
    assert!(stats_result.max <= 255.0);
    assert!(stats_result.mean > 0.0);
    assert!(stats_result.median.is_some());
}

#[test]
fn test_pixel_statistics_empty() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("empty.dcm");

    let pixels = vec![];
    create_test_dicom_with_pixels(&path, pixels);

    let stats_result = stats::pixel_statistics_for_file(&path).expect("stats");

    assert_eq!(stats_result.total_pixels, 0);
    assert_eq!(stats_result.min, 0.0);
    assert_eq!(stats_result.max, 0.0);
    assert_eq!(stats_result.mean, 0.0);
}

#[test]
fn test_pixel_format_summary() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("format.dcm");

    let pixels = vec![0_u8, 1, 2, 3];
    create_test_dicom_with_pixels(&path, pixels);

    let format = stats::pixel_format_for_file(&path).expect("format");

    assert_eq!(format.rows, 2);
    assert_eq!(format.columns, 2);
    assert_eq!(format.samples_per_pixel, 1);
    assert_eq!(format.bits_allocated, 8);
    assert_eq!(format.bits_stored, 8);
    assert_eq!(format.high_bit, 7);
}

#[test]
fn test_histogram() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("hist.dcm");

    // Criar imagem com valores distribuídos
    let pixels: Vec<u8> = (0u8..=255).collect();
    create_test_dicom_with_pixels(&path, pixels);

    let histogram = stats::histogram_for_file(&path, 10).expect("histogram");

    assert_eq!(histogram.bins.len(), 10);
    assert!(histogram.min >= 0.0);
    assert!(histogram.max <= 255.0);
    
    // Verificar que todos os bins têm contagem > 0 (distribuição uniforme)
    let total_count: u64 = histogram.bins.iter().sum();
    assert!(total_count > 0);
}

#[test]
fn test_histogram_empty() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("empty_hist.dcm");

    let pixels = vec![];
    create_test_dicom_with_pixels(&path, pixels);

    let histogram = stats::histogram_for_file(&path, 10).expect("histogram");

    assert_eq!(histogram.bins.len(), 0);
    assert_eq!(histogram.min, 0.0);
    assert_eq!(histogram.max, 0.0);
}


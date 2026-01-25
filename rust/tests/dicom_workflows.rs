//
// dicom_workflows.rs
// Dicom-Tools-rs
//
// Integration-style tests covering metadata extraction, validation, pixel stats, image export, anonymization, transcoding, and JSON round-trips.
//
// Thales Matheus Mendonça Santos - November 2025

use std::{env, path::PathBuf};

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::{EXPLICIT_VR_LITTLE_ENDIAN, IMPLICIT_VR_LITTLE_ENDIAN};
use dicom_tools::models::InfoReport;
use dicom_tools::{anonymize, dump, image, json, metadata, scu, stats, transcode, validate};
use serde_json::Value;
use tempfile::{tempdir, TempDir};

fn build_test_dicom() -> (TempDir, PathBuf) {
    // Construct a tiny Secondary Capture instance with predictable pixel values.
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("sample.dcm");

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
        Tag(0x0008, 0x0060),
        VR::CS,
        PrimitiveValue::from("OT"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0020),
        VR::DA,
        PrimitiveValue::from("20240101"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0016),
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        Tag(0x0008, 0x0018),
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.1"),
    ));

    obj.put(DataElement::new(
        Tag(0x0028, 0x0010),
        VR::US,
        PrimitiveValue::from(2_u16),
    )); // Rows
    obj.put(DataElement::new(
        Tag(0x0028, 0x0011),
        VR::US,
        PrimitiveValue::from(2_u16),
    )); // Columns
    obj.put(DataElement::new(
        Tag(0x0028, 0x0002),
        VR::US,
        PrimitiveValue::from(1_u16),
    )); // Samples per pixel
    obj.put(DataElement::new(
        Tag(0x0028, 0x0100),
        VR::US,
        PrimitiveValue::from(8_u16),
    )); // Bits Allocated
    obj.put(DataElement::new(
        Tag(0x0028, 0x0101),
        VR::US,
        PrimitiveValue::from(8_u16),
    )); // Bits Stored
    obj.put(DataElement::new(
        Tag(0x0028, 0x0102),
        VR::US,
        PrimitiveValue::from(7_u16),
    )); // High Bit
    obj.put(DataElement::new(
        Tag(0x0028, 0x0103),
        VR::US,
        PrimitiveValue::from(0_u16),
    )); // Pixel Representation
    obj.put(DataElement::new(
        Tag(0x0028, 0x0004),
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        Tag(0x0028, 0x0008),
        VR::IS,
        PrimitiveValue::from("1"),
    )); // Number of Frames
    obj.put(DataElement::new(
        Tag(0x0028, 0x1052),
        VR::DS,
        PrimitiveValue::from("-1024"),
    )); // Rescale Intercept
    obj.put(DataElement::new(
        Tag(0x0028, 0x1053),
        VR::DS,
        PrimitiveValue::from("2"),
    )); // Rescale Slope
    obj.put(DataElement::new(
        Tag(0x0028, 0x1050),
        VR::DS,
        PrimitiveValue::from("50"),
    )); // Window Center
    obj.put(DataElement::new(
        Tag(0x0028, 0x1051),
        VR::DS,
        PrimitiveValue::from("150"),
    )); // Window Width

    obj.put(DataElement::new(
        Tag(0x7fe0, 0x0010),
        VR::OB,
        PrimitiveValue::from(vec![0, 64, 128, 255]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.1")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write test dicom");

    (dir, path)
}

#[test]
fn metadata_and_validation_cover_required_tags() {
    let (_dir, path) = build_test_dicom();

    // Verify that the CLI-friendly metadata struct is populated.
    let basic = metadata::read_basic_metadata(&path).expect("basic metadata");
    assert_eq!(basic.patient_name.as_deref(), Some("Test^Patient"));
    assert_eq!(basic.modality.as_deref(), Some("OT"));
    assert!(basic.has_pixel_data);

    let obj = dicom::object::open_file(&path).expect("open file");
    let report = validate::validate_obj(&obj);
    assert!(report.valid);
    assert!(report.has_pixel_data);
}

#[test]
fn pixel_stats_and_image_preview_work() {
    let (_dir, path) = build_test_dicom();

    // Ensure that basic statistics are computed and the image renderer emits PNG bytes.
    let stats = stats::pixel_statistics_for_file(&path).expect("stats");
    assert_eq!(stats.total_pixels, 4);
    assert!((stats.min - -1024.0).abs() < f32::EPSILON);
    assert!((stats.max - -514.0).abs() < f32::EPSILON);
    assert!((stats.mean - -800.5).abs() < 0.1);
    let median = stats.median.unwrap_or_default();
    assert!(median < -830.0 && median > -834.0);

    let png = image::first_frame_png_bytes(&path).expect("render png");
    assert!(png.starts_with(&[0x89, b'P', b'N', b'G']));
}

#[test]
fn anonymization_creates_clean_copy() {
    let (_dir, path) = build_test_dicom();
    let output = path.with_file_name("sample_anon.dcm");

    anonymize::process_file(&path, Some(output.clone())).expect("anonymize");
    let anon = dicom::object::open_file(&output).expect("open anon");

    let patient_name = anon
        .element(Tag(0x0010, 0x0010))
        .expect("name")
        .to_str()
        .unwrap();
    assert_eq!(patient_name, "ANONYMOUS^PATIENT");
}

#[test]
fn transcode_keeps_pixel_data_intact() {
    let (_dir, path) = build_test_dicom();
    let output = path.with_file_name("sample_transcoded.dcm");

    transcode::transcode(
        &path,
        &output,
        transcode::UncompressedTransferSyntax::ExplicitVRLittleEndian,
    )
    .expect("transcode");

    let baseline = stats::pixel_statistics_for_file(&path).expect("baseline stats");
    let transcoded = stats::pixel_statistics_for_file(&output).expect("transcoded stats");

    assert_eq!(baseline.total_pixels, transcoded.total_pixels);
    assert!((baseline.min - transcoded.min).abs() < f32::EPSILON);
    assert!((baseline.max - transcoded.max).abs() < f32::EPSILON);
}

#[test]
fn transcode_to_implicit_vr_le_changes_meta() {
    let (_dir, path) = build_test_dicom();
    let output = path.with_file_name("sample_transcoded_implicit.dcm");

    transcode::transcode(
        &path,
        &output,
        transcode::UncompressedTransferSyntax::ImplicitVRLittleEndian,
    )
    .expect("transcode implicit");

    let transcoded = dicom::object::open_file(&output).expect("open transcoded");
    let ts_uid = transcoded.meta().transfer_syntax();
    assert_eq!(
        ts_uid,
        dicom::transfer_syntax::entries::IMPLICIT_VR_LITTLE_ENDIAN.uid()
    );
}

#[test]
fn transcode_handles_all_uncompressed_variants() {
    let (_dir, path) = build_test_dicom();
    let baseline = stats::pixel_statistics_for_file(&path).expect("baseline stats");

    let variants = [
        (
            transcode::UncompressedTransferSyntax::ExplicitVRLittleEndian,
            EXPLICIT_VR_LITTLE_ENDIAN.uid(),
            "explicit",
        ),
        (
            transcode::UncompressedTransferSyntax::ImplicitVRLittleEndian,
            IMPLICIT_VR_LITTLE_ENDIAN.uid(),
            "implicit",
        ),
    ];

    for (syntax, expected_uid, label) in variants {
        let output = path.with_file_name(format!("sample_transcoded_{label}.dcm"));
        transcode::transcode(&path, &output, syntax).expect("transcode variant");
        let stats_out = stats::pixel_statistics_for_file(&output).expect("stats");

        assert_eq!(baseline.total_pixels, stats_out.total_pixels);
        assert!((baseline.min - stats_out.min).abs() < f32::EPSILON);
        assert!((baseline.max - stats_out.max).abs() < f32::EPSILON);

        let transcoded = dicom::object::open_file(&output).expect("open transcoded");
        assert_eq!(transcoded.meta().transfer_syntax(), expected_uid);
    }
}

#[test]
fn json_roundtrip_preserves_pixels_and_attributes() {
    let (_dir, path) = build_test_dicom();
    let json_path = path.with_file_name("sample.json");
    let roundtrip = path.with_file_name("sample_roundtrip.dcm");

    json::to_json(&path, Some(&json_path)).expect("to json");
    json::from_json(&json_path, &roundtrip).expect("from json");

    let original = dicom::object::open_file(&path).expect("open original");
    let restored = dicom::object::open_file(&roundtrip).expect("open roundtrip");

    let original_name = original
        .element(Tag(0x0010, 0x0010))
        .expect("name")
        .to_str()
        .unwrap();
    let restored_name = restored
        .element(Tag(0x0010, 0x0010))
        .expect("name")
        .to_str()
        .unwrap();
    assert_eq!(original_name, restored_name);

    let original_pixels = original
        .element(Tag(0x7FE0, 0x0010))
        .expect("pixels")
        .to_bytes()
        .unwrap()
        .into_owned();
    let restored_pixels = restored
        .element(Tag(0x7FE0, 0x0010))
        .expect("pixels")
        .to_bytes()
        .unwrap()
        .into_owned();
    assert_eq!(original_pixels, restored_pixels);
}

#[test]
fn basic_metadata_exposes_dimensions_and_frames() {
    let (_dir, path) = build_test_dicom();
    let basic = metadata::read_basic_metadata(&path).expect("basic");

    assert_eq!(basic.rows, Some(2));
    assert_eq!(basic.columns, Some(2));
    assert_eq!(basic.number_of_frames, Some(1));
    assert!(basic.transfer_syntax.is_some());
}

#[test]
fn info_json_includes_basic_and_pixel_format() {
    let (_dir, path) = build_test_dicom();
    let json_str = metadata::info_to_json(&path).expect("info json");

    let report: InfoReport = serde_json::from_str(&json_str).expect("deserialize info report");
    assert_eq!(report.basic.patient_name.as_deref(), Some("Test^Patient"));
    assert_eq!(
        report.detailed.patient.get("Name").map(String::as_str),
        Some("Test^Patient")
    );
    assert!(report.pixel_format.is_some());
}

#[test]
fn dump_json_contains_standard_tags() {
    let (_dir, path) = build_test_dicom();
    let json_str = dump::dump_to_json(&path).expect("dump json");
    let value: Value = serde_json::from_str(&json_str).expect("parse json");

    assert_eq!(value["00080060"]["Value"][0].as_str(), Some("OT"));
    assert_eq!(
        value["00100010"]["Value"][0]["Alphabetic"].as_str(),
        Some("Test^Patient")
    );
}

#[test]
fn histogram_counts_align_with_pixels() {
    let (_dir, path) = build_test_dicom();
    let histogram = stats::histogram_for_file(&path, 8).expect("histogram");
    let total: u64 = histogram.bins.iter().sum();
    assert_eq!(total, 4);
    assert_eq!(histogram.bins.len(), 8);
    assert!(histogram.max >= histogram.min);
}

#[test]
fn histogram_respects_requested_bins() {
    let (_dir, path) = build_test_dicom();
    let histogram = stats::histogram_for_file(&path, 4).expect("histogram");

    assert_eq!(histogram.bins.len(), 4);
    assert_eq!(histogram.bins, vec![1, 1, 1, 1]);
}

#[test]
fn pixel_format_summary_includes_window_and_rescale() {
    let (_dir, path) = build_test_dicom();
    let details = stats::pixel_format_for_file(&path).expect("pixel format");

    assert_eq!(details.samples_per_pixel, 1);
    assert_eq!(details.bits_allocated, 8);
    assert_eq!(details.bits_stored, 8);
    assert_eq!(details.pixel_representation, "Unsigned");
    assert_eq!(details.rescale_intercept, Some(-1024.0));
    assert_eq!(details.rescale_slope, Some(2.0));
    assert_eq!(details.window_center, Some(50.0));
    assert_eq!(details.window_width, Some(150.0));
}

#[test]
#[ignore = "Requires TEST_PACS_ADDR pointing to host:port for C-ECHO"]
fn echo_against_configured_pacs() {
    let addr = env::var("TEST_PACS_ADDR").expect("TEST_PACS_ADDR not set");
    scu::echo(&addr).expect("echo");
}

#[test]
#[ignore = "Requires TEST_PACS_ADDR pointing to host:port for C-STORE"]
fn push_against_configured_pacs() {
    let addr = env::var("TEST_PACS_ADDR").expect("TEST_PACS_ADDR not set");
    let (_dir, path) = build_test_dicom();
    scu::push(&addr, &path).expect("push");
}

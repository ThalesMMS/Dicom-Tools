//
// new_features.rs
// Dicom-Tools-rs
//
// Coverage for recent feature requests: multi-frame functional groups, per-frame VOI, and affine reconstruction.
//
// Thales Matheus Mendonça Santos - November 2025

mod support;

use dicom::dictionary_std::tags;
use dicom_tools::{functional_groups, image, metadata, stats, structured, scu};
use dicom_tools::structured::PathSegment;
use support::{build_multiframe_fg_dicom, build_sr_like_dicom, spawn_fake_find_scp};

#[test]
fn per_frame_window_levels_from_fg_are_preserved() {
    let (_dir, path) = build_multiframe_fg_dicom();

    let format = stats::pixel_format_for_file(&path).expect("pixel format");
    let per_frame = format
        .per_frame_voi
        .as_ref()
        .expect("per-frame VOI entries");

    assert_eq!(per_frame.len(), 3);
    assert_eq!(per_frame[0].window_center, Some(10.0));
    assert_eq!(per_frame[0].window_width, Some(20.0));
    assert_eq!(per_frame[1].window_center, Some(60.0));
    assert_eq!(per_frame[1].window_width, Some(30.0));
    assert_eq!(per_frame[2].window_center, Some(100.0));
    assert_eq!(per_frame[2].window_width, Some(40.0));
    assert_ne!(per_frame[0].window_center, per_frame[1].window_center);
}

#[test]
fn functional_groups_affine_matches_positions() {
    let (_dir, path) = build_multiframe_fg_dicom();

    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");
    assert_eq!(geometries.len(), 3);

    let g0 = &geometries[0];
    let g1 = &geometries[1];
    let g2 = &geometries[2];

    assert_eq!(g0.frame_index, 0);
    assert_eq!(g0.pixel_spacing, [0.5, 0.5]);
    assert!((g0.slice_vector[2] - 2.0).abs() < 1e-6);
    assert!((g1.affine[2][3] - 2.0).abs() < 1e-6);
    assert!((g2.affine[2][3] - 4.0).abs() < 1e-6);
    assert!((g0.affine[0][0] - 0.5).abs() < 1e-6);
    assert!((g0.affine[1][1] - 0.5).abs() < 1e-6);
}

#[test]
fn structured_path_navigation_reads_nested_sequences() {
    let (_dir, path) = build_sr_like_dicom();

    let text_path = [
        PathSegment::item(tags::CONTENT_SEQUENCE, 0),
        PathSegment::item(tags::CONTENT_SEQUENCE, 0),
        PathSegment::item(tags::CONTENT_SEQUENCE, 0),
        PathSegment::element(tags::TEXT_VALUE),
    ];
    let text = structured::value_at_path_from_file(&path, &text_path).expect("path lookup");
    assert_eq!(text.as_deref(), Some("Lesion size 3mm"));

    let concept_path = [
        PathSegment::item(tags::CONTENT_SEQUENCE, 0),
        PathSegment::item(tags::CONCEPT_NAME_CODE_SEQUENCE, 0),
        PathSegment::element(tags::CODE_MEANING),
    ];
    let meaning = structured::value_at_path_from_file(&path, &concept_path).expect("path lookup");
    assert_eq!(meaning.as_deref(), Some("Findings"));
}

#[test]
fn lazy_frame_read_is_frame_scoped() {
    let (_dir, path) = build_multiframe_fg_dicom();

    let frame0 = image::read_frame_lazy(&path, 0).expect("frame 0");
    let frame2 = image::read_frame_lazy(&path, 2).expect("frame 2");

    assert_eq!(frame0, vec![0, 10, 20, 30]);
    assert_eq!(frame2, vec![80, 90, 100, 110]);
}

#[test]
fn metadata_access_without_pixel_decode() {
    let (_dir, path) = build_multiframe_fg_dicom();
    let basic = metadata::read_basic_metadata(&path).expect("basic metadata");

    assert_eq!(basic.number_of_frames, Some(3));
    assert!(basic.has_pixel_data);
}

#[test]
fn cfind_handles_pending_and_final_responses() {
    let (handle, addr) = spawn_fake_find_scp();

    let matches = scu::find(&addr).expect("cfind");
    assert!(
        matches.iter().any(|m| m.status == 0xFF00),
        "missing pending status"
    );
    assert!(
        matches.iter().any(|m| m.status == 0x0000),
        "missing final status"
    );

    let pending = matches
        .iter()
        .find(|m| m.status == 0xFF00)
        .expect("pending match");
    assert_eq!(pending.patient_name.as_deref(), Some("FIND^PATIENT"));
    assert_eq!(pending.study_instance_uid.as_deref(), Some("1.2.3.4"));

    handle.join().expect("server thread");
}

#[test]
fn pixel_summary_matches_reference_values() {
    let (_dir, path) = build_multiframe_fg_dicom();

    let format = stats::pixel_format_for_file(&path).expect("pixel format");
    assert_eq!(format.bits_allocated, 8);
    assert_eq!(format.number_of_frames, 3);

    let histogram = stats::histogram_for_file(&path, 4).expect("histogram");
    assert_eq!(histogram.bins, vec![3, 3, 3, 3]);

    let pixel_stats = stats::pixel_statistics_for_file(&path).expect("stats");
    assert_eq!(pixel_stats.total_pixels, 12);
    assert!((pixel_stats.min - 0.0).abs() < f32::EPSILON);
    assert!((pixel_stats.max - 110.0).abs() < f32::EPSILON);
    assert!((pixel_stats.mean - 55.0).abs() < 0.01);
}

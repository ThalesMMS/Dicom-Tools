//
// functional_groups_tests.rs
// Dicom-Tools-rs
//
// Tests for frame geometry extraction from functional groups.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::dictionary_std::tags;
use dicom_tools::functional_groups;

mod support;
use support::{build_multiframe_fg_dicom, build_singleframe_fg_dicom};

#[test]
fn test_frame_geometries_from_multiframe_file() {
    let (_dir, path) = build_multiframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");

    assert_eq!(geometries.len(), 3);

    // Verify that each frame has a different position.
    let positions: Vec<_> = geometries
        .iter()
        .map(|g| g.image_position_patient[2])
        .collect();
    assert_eq!(positions[0], 0.0);
    assert_eq!(positions[1], 2.0);
    assert_eq!(positions[2], 4.0);

    // Verify that pixel spacing is present.
    for geo in &geometries {
        assert_eq!(geo.pixel_spacing, [0.5, 0.5]);
    }

    // Verify that the affine matrix is present.
    for geo in &geometries {
        assert_eq!(geo.affine[3][3], 1.0);
        assert_eq!(geo.affine[3][0..3], [0.0, 0.0, 0.0]);
    }
}

#[test]
fn test_frame_geometries_single_frame() {
    let (_dir, path) = build_singleframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");
    assert_eq!(geometries.len(), 1);

    let geometry = &geometries[0];
    assert_eq!(geometry.image_position_patient, [0.0, 0.0, 0.0]);
    assert_eq!(
        geometry.image_orientation_patient,
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    );
    assert_eq!(geometry.pixel_spacing, [0.5, 0.5]);
    assert_eq!(geometry.slice_vector, [0.0, 0.0, 2.0]);
    assert_eq!(geometry.affine[3], [0.0, 0.0, 0.0, 1.0]);
}

#[test]
fn test_frame_geometries_orientation() {
    let (_dir, path) = build_multiframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");

    // Verify that orientation is normalized.
    for geo in &geometries {
        let row = &geo.image_orientation_patient[0..3];
        let col = &geo.image_orientation_patient[3..6];
        
        // Verify that the vectors have magnitude close to 1.0.
        let row_mag = (row[0] * row[0] + row[1] * row[1] + row[2] * row[2]).sqrt();
        let col_mag = (col[0] * col[0] + col[1] * col[1] + col[2] * col[2]).sqrt();
        
        assert!((row_mag - 1.0).abs() < 0.01);
        assert!((col_mag - 1.0).abs() < 0.01);
    }
}

#[test]
fn test_frame_geometries_slice_vector() {
    let (_dir, path) = build_multiframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");

    // Verify that slice_vector is present and non-zero.
    for geo in &geometries {
        let slice_mag = (geo.slice_vector[0] * geo.slice_vector[0]
            + geo.slice_vector[1] * geo.slice_vector[1]
            + geo.slice_vector[2] * geo.slice_vector[2])
            .sqrt();
        assert!(slice_mag > 0.0);
    }
}

#[test]
fn test_functional_group_fixtures_use_distinct_sop_instance_uids() {
    let (_multi_dir, multi_path) = build_multiframe_fg_dicom();
    let (_single_dir, single_path) = build_singleframe_fg_dicom();

    let multi = dicom::object::open_file(&multi_path).expect("open multiframe file");
    let single = dicom::object::open_file(&single_path).expect("open single-frame file");
    let multi_uid = multi
        .element(tags::SOP_INSTANCE_UID)
        .expect("multi SOP Instance UID")
        .to_str()
        .expect("multi UID string");
    let single_uid = single
        .element(tags::SOP_INSTANCE_UID)
        .expect("single SOP Instance UID")
        .to_str()
        .expect("single UID string");

    assert_ne!(multi_uid, single_uid);
}

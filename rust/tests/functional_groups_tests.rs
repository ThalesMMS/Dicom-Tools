//
// functional_groups_tests.rs
// Dicom-Tools-rs
//
// Testes para extração de geometria de frames a partir de grupos funcionais.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom_tools::functional_groups;

mod support;
use support::build_multiframe_fg_dicom;

#[test]
fn test_frame_geometries_from_multiframe_file() {
    let (_dir, path) = support::build_multiframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");

    assert_eq!(geometries.len(), 3);

    // Verificar que cada frame tem uma posição diferente
    let positions: Vec<_> = geometries
        .iter()
        .map(|g| g.image_position_patient[2])
        .collect();
    assert_eq!(positions[0], 0.0);
    assert_eq!(positions[1], 2.0);
    assert_eq!(positions[2], 4.0);

    // Verificar que pixel spacing está presente
    for geo in &geometries {
        assert_eq!(geo.pixel_spacing, [0.5, 0.5]);
    }

    // Verificar que affine matrix está presente
    for geo in &geometries {
        assert_eq!(geo.affine[3][3], 1.0);
        assert_eq!(geo.affine[3][0..3], [0.0, 0.0, 0.0]);
    }
}

#[test]
fn test_frame_geometries_single_frame() {
    let (_dir, path) = support::build_multiframe_fg_dicom();
    // Modificar para ter apenas 1 frame
    // Por enquanto, testamos que funciona com o arquivo existente
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");
    assert!(!geometries.is_empty());
}

#[test]
fn test_frame_geometries_orientation() {
    let (_dir, path) = support::build_multiframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");

    // Verificar que a orientação está normalizada
    for geo in &geometries {
        let row = &geo.image_orientation_patient[0..3];
        let col = &geo.image_orientation_patient[3..6];
        
        // Verificar que os vetores têm magnitude próxima de 1.0
        let row_mag = (row[0] * row[0] + row[1] * row[1] + row[2] * row[2]).sqrt();
        let col_mag = (col[0] * col[0] + col[1] * col[1] + col[2] * col[2]).sqrt();
        
        assert!((row_mag - 1.0).abs() < 0.01);
        assert!((col_mag - 1.0).abs() < 0.01);
    }
}

#[test]
fn test_frame_geometries_slice_vector() {
    let (_dir, path) = support::build_multiframe_fg_dicom();
    let geometries = functional_groups::frame_geometries_for_file(&path).expect("geometries");

    // Verificar que slice_vector está presente e não é zero
    for geo in &geometries {
        let slice_mag = (geo.slice_vector[0] * geo.slice_vector[0]
            + geo.slice_vector[1] * geo.slice_vector[1]
            + geo.slice_vector[2] * geo.slice_vector[2])
            .sqrt();
        assert!(slice_mag > 0.0);
    }
}


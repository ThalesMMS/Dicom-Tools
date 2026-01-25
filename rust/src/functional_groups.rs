//
// functional_groups.rs
// Dicom-Tools-rs
//
// Helpers to extract per-frame spatial metadata from functional groups and rebuild affine matrices.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::{Context, Result};
use dicom::core::value::Value;
use dicom::core::Tag;
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::{open_file, DefaultDicomObject, InMemDicomObject};
use std::path::Path;

use crate::models::FrameGeometry;

type Obj = InMemDicomObject<StandardDataDictionary>;

/// Compute per-frame spatial metadata (orientation, position, pixel spacing, affine) for a file.
pub fn frame_geometries_for_file(path: &Path) -> Result<Vec<FrameGeometry>> {
    let obj = open_file(path).context("Failed to open DICOM file")?;
    frame_geometries(&obj)
}

/// Compute per-frame spatial metadata (orientation, position, pixel spacing, affine) for an object.
pub fn frame_geometries(obj: &DefaultDicomObject) -> Result<Vec<FrameGeometry>> {
    let number_of_frames = obj
        .element(tags::NUMBER_OF_FRAMES)
        .ok()
        .and_then(|e| e.to_int::<i32>().ok())
        .unwrap_or(1)
        .max(1) as usize;

    let shared_item = shared_fg_item(obj);
    let per_frame_items = per_frame_items(obj);

    let orientation_shared = shared_item
        .as_ref()
        .and_then(orientation_from_item)
        .or_else(|| orientation_direct(obj))
        .unwrap_or([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]);
    let position_shared = shared_item
        .as_ref()
        .and_then(position_from_item)
        .or_else(|| position_direct(obj))
        .unwrap_or([0.0, 0.0, 0.0]);
    let pixel_spacing_shared = shared_item
        .as_ref()
        .and_then(pixel_spacing_from_item)
        .or_else(|| pixel_spacing_direct(obj))
        .unwrap_or([1.0, 1.0]);
    let spacing_between_slices = shared_item
        .as_ref()
        .and_then(spacing_between_slices_from_item)
        .or_else(|| spacing_between_slices_direct(obj));

    let mut frames_raw = Vec::with_capacity(number_of_frames);
    for idx in 0..number_of_frames {
        let per_frame_item = per_frame_items.get(idx);
        let orientation = per_frame_item
            .and_then(orientation_from_item)
            .unwrap_or(orientation_shared);
        let position = per_frame_item
            .and_then(position_from_item)
            .unwrap_or(position_shared);
        let pixel_spacing = per_frame_item
            .and_then(pixel_spacing_from_item)
            .unwrap_or(pixel_spacing_shared);
        let slice_spacing = per_frame_item
            .and_then(spacing_between_slices_from_item)
            .or(spacing_between_slices);

        frames_raw.push((orientation, position, pixel_spacing, slice_spacing));
    }

    let mut geometries = Vec::with_capacity(number_of_frames);
    for idx in 0..number_of_frames {
        let (orientation, position, pixel_spacing, slice_spacing) = frames_raw[idx];
        let row = [orientation[0], orientation[1], orientation[2]];
        let col = [orientation[3], orientation[4], orientation[5]];
        let row = normalize(row);
        let col = normalize(col);
        let normal = normalize(cross(row, col));

        let slice_step = slice_spacing.unwrap_or_else(|| {
            if number_of_frames > 1 {
                // Prefer the next frame when available, otherwise fall back to the previous one.
                let neighbor = if idx + 1 < number_of_frames {
                    idx + 1
                } else {
                    idx.saturating_sub(1)
                };
                let neighbor_pos = frames_raw[neighbor].1;
                let diff = [
                    neighbor_pos[0] - position[0],
                    neighbor_pos[1] - position[1],
                    neighbor_pos[2] - position[2],
                ];
                let step = dot(diff, normal).abs();
                if step > 0.0 { step } else { 1.0 }
            } else {
                1.0
            }
        });

        let slice_vector = [
            normal[0] * slice_step,
            normal[1] * slice_step,
            normal[2] * slice_step,
        ];

        let affine = [
            [
                row[0] * pixel_spacing[0],
                col[0] * pixel_spacing[1],
                slice_vector[0],
                position[0],
            ],
            [
                row[1] * pixel_spacing[0],
                col[1] * pixel_spacing[1],
                slice_vector[1],
                position[1],
            ],
            [
                row[2] * pixel_spacing[0],
                col[2] * pixel_spacing[1],
                slice_vector[2],
                position[2],
            ],
            [0.0, 0.0, 0.0, 1.0],
        ];

        geometries.push(FrameGeometry {
            frame_index: idx as u32,
            image_position_patient: position,
            image_orientation_patient: [
                row[0], row[1], row[2], col[0], col[1], col[2],
            ],
            pixel_spacing,
            slice_vector,
            affine,
        });
    }

    Ok(geometries)
}

fn shared_fg_item(obj: &DefaultDicomObject) -> Option<Obj> {
    let elem = obj.get(tags::SHARED_FUNCTIONAL_GROUPS_SEQUENCE)?;
    match elem.value() {
        Value::Sequence(seq) => seq.items().first().cloned(),
        _ => None,
    }
}

fn per_frame_items(obj: &DefaultDicomObject) -> Vec<Obj> {
    obj.get(tags::PER_FRAME_FUNCTIONAL_GROUPS_SEQUENCE)
        .and_then(|elem| match elem.value() {
            Value::Sequence(seq) => Some(seq.items().to_vec()),
            _ => None,
        })
        .unwrap_or_default()
}

fn orientation_from_item(item: &Obj) -> Option<[f64; 6]> {
    sequence_values(item, tags::PLANE_ORIENTATION_SEQUENCE, tags::IMAGE_ORIENTATION_PATIENT)
        .and_then(|vals| to_array6(&vals))
}

fn position_from_item(item: &Obj) -> Option<[f64; 3]> {
    sequence_values(item, tags::PLANE_POSITION_SEQUENCE, tags::IMAGE_POSITION_PATIENT)
        .and_then(|vals| to_array3(&vals))
        .or_else(|| direct_multi(item, tags::IMAGE_POSITION_PATIENT).and_then(|vals| to_array3(&vals)))
}

fn pixel_spacing_from_item(item: &Obj) -> Option<[f64; 2]> {
    sequence_values(item, tags::PIXEL_MEASURES_SEQUENCE, tags::PIXEL_SPACING)
        .and_then(|vals| to_array2(&vals))
        .or_else(|| direct_multi(item, tags::PIXEL_SPACING).and_then(|vals| to_array2(&vals)))
}

fn spacing_between_slices_from_item(item: &Obj) -> Option<f64> {
    sequence_values(
        item,
        tags::PIXEL_MEASURES_SEQUENCE,
        tags::SPACING_BETWEEN_SLICES,
    )
    .and_then(|vals| vals.first().copied())
    .or_else(|| direct_scalar(item, tags::SPACING_BETWEEN_SLICES))
}

fn orientation_direct(obj: &DefaultDicomObject) -> Option<[f64; 6]> {
    obj.element(tags::IMAGE_ORIENTATION_PATIENT)
        .ok()
        .and_then(|e| e.to_multi_float64().ok())
        .and_then(|vals| to_array6(&vals))
}

fn position_direct(obj: &DefaultDicomObject) -> Option<[f64; 3]> {
    obj.element(tags::IMAGE_POSITION_PATIENT)
        .ok()
        .and_then(|e| e.to_multi_float64().ok())
        .and_then(|vals| to_array3(&vals))
}

fn pixel_spacing_direct(obj: &DefaultDicomObject) -> Option<[f64; 2]> {
    obj.element(tags::PIXEL_SPACING)
        .ok()
        .and_then(|e| e.to_multi_float64().ok())
        .and_then(|vals| to_array2(&vals))
}

fn spacing_between_slices_direct(obj: &DefaultDicomObject) -> Option<f64> {
    obj.element(tags::SPACING_BETWEEN_SLICES)
        .ok()
        .and_then(|e| e.to_float64().ok())
}

fn sequence_values(item: &Obj, seq_tag: Tag, inner_tag: Tag) -> Option<Vec<f64>> {
    let seq = item.get(seq_tag)?;
    let first = match seq.value() {
        Value::Sequence(seq) => seq.items().first()?,
        _ => return None,
    };
    direct_multi(first, inner_tag)
}

fn direct_multi(item: &Obj, tag: Tag) -> Option<Vec<f64>> {
    item.element(tag).ok()?.to_multi_float64().ok()
}

fn direct_scalar(item: &Obj, tag: Tag) -> Option<f64> {
    item.element(tag).ok()?.to_float64().ok()
}

fn to_array2(values: &[f64]) -> Option<[f64; 2]> {
    if values.len() >= 2 {
        Some([values[0], values[1]])
    } else {
        None
    }
}

fn to_array3(values: &[f64]) -> Option<[f64; 3]> {
    if values.len() >= 3 {
        Some([values[0], values[1], values[2]])
    } else {
        None
    }
}

fn to_array6(values: &[f64]) -> Option<[f64; 6]> {
    if values.len() >= 6 {
        Some([
            values[0],
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
        ])
    } else {
        None
    }
}

fn cross(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}

fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

fn normalize(v: [f64; 3]) -> [f64; 3] {
    let norm = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt();
    if norm == 0.0 {
        [0.0, 0.0, 1.0]
    } else {
        [v[0] / norm, v[1] / norm, v[2] / norm]
    }
}

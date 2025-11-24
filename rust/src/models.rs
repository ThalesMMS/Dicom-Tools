//
// models.rs
// Dicom-Tools-rs
//
// Defines serializable data structures for metadata, validation, pixel statistics, and histograms.
//
// Thales Matheus Mendonça Santos - November 2025

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

/// Lightweight fields shown in CLI summaries and quick API responses.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BasicMetadata {
    pub patient_name: Option<String>,
    pub patient_id: Option<String>,
    pub study_date: Option<String>,
    pub modality: Option<String>,
    pub sop_class_uid: Option<String>,
    pub has_pixel_data: bool,
    pub transfer_syntax: Option<String>,
    pub rows: Option<u32>,
    pub columns: Option<u32>,
    pub number_of_frames: Option<u32>,
}

/// Expanded, categorized metadata suitable for UI rendering.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetailedMetadata {
    pub patient: BTreeMap<String, String>,
    pub study: BTreeMap<String, String>,
    pub image: BTreeMap<String, String>,
    pub misc: BTreeMap<String, String>,
}

/// High-level validation report for required attributes and pixel presence.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationSummary {
    pub valid: bool,
    pub missing_tags: Vec<String>,
    pub has_pixel_data: bool,
}

/// Aggregate statistics over pixel values.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PixelStatistics {
    pub min: f32,
    pub max: f32,
    pub mean: f32,
    pub median: Option<f32>,
    pub std_dev: f32,
    pub total_pixels: usize,
    pub shape: Vec<usize>,
}

/// Histogram buckets alongside the observed range.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PixelHistogram {
    pub bins: Vec<u64>,
    pub min: f32,
    pub max: f32,
}

/// Summary of pixel encoding and VOI/LUT hints.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PixelFormatSummary {
    pub rows: u32,
    pub columns: u32,
    pub number_of_frames: u32,
    pub samples_per_pixel: u16,
    pub photometric_interpretation: String,
    pub planar_configuration: Option<String>,
    pub bits_allocated: u16,
    pub bits_stored: u16,
    pub high_bit: u16,
    pub pixel_representation: String,
    pub rescale_slope: Option<f64>,
    pub rescale_intercept: Option<f64>,
    pub window_center: Option<f64>,
    pub window_width: Option<f64>,
}

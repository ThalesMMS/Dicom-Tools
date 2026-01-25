//
// stats.rs
// Dicom-Tools-rs
//
// Computes pixel statistics, histograms, and format summaries from decoded DICOM pixel data.
//
// Thales Matheus Mendonça Santos - November 2025

use std::path::Path;

use anyhow::{Context, Result};
use dicom::object::open_file;
use dicom::pixeldata::PixelDecoder;
use dicom_pixeldata::{ConvertOptions, DecodedPixelData, ModalityLutOption, Rescale, WindowLevel};
use dicom::dictionary_std::tags;
use dicom_core::header::HasLength;

use crate::models::{FrameVoi, PixelFormatSummary, PixelHistogram, PixelStatistics};

/// Calculate and print basic statistics of the pixel data.
pub fn stats(input: &Path) -> Result<()> {
    let stats = pixel_statistics_for_file(input)?;

    // Present data in a CLI-friendly block.
    println!("Statistics for {:?}", input);
    println!("  Shape: {:?}", stats.shape);
    println!("  Min:   {:.2}", stats.min);
    println!("  Max:   {:.2}", stats.max);
    println!("  Mean:  {:.2}", stats.mean);
    if let Some(median) = stats.median {
        println!("  Median:{:.2}", median);
    }
    println!("  StdDv: {:.2}", stats.std_dev);
    println!("  Total Pixels: {}", stats.total_pixels);

    Ok(())
}

pub fn pixel_statistics_for_file(input: &Path) -> Result<PixelStatistics> {
    let obj = open_file(input).context("Failed to open DICOM file")?;
    // Handle empty pixel data gracefully by short-circuiting.
    if let Ok(elem) = obj.element(tags::PIXEL_DATA) {
        if elem.value().length().0 == 0 {
            return Ok(PixelStatistics {
                min: 0.0,
                max: 0.0,
                mean: 0.0,
                median: None,
                std_dev: 0.0,
                total_pixels: 0,
                shape: vec![],
            });
        }
    }

    match obj.decode_pixel_data() {
        Ok(decoded) => pixel_statistics_from_decoded(&decoded),
        Err(err) => {
            // Some files declare pixel metadata but contain no samples; treat as empty instead of hard error.
            let msg = format!("{err}");
            if msg.contains("Frame #0 is out of range") || msg.contains("no pixel data") {
                Ok(PixelStatistics {
                    min: 0.0,
                    max: 0.0,
                    mean: 0.0,
                    median: None,
                    std_dev: 0.0,
                    total_pixels: 0,
                    shape: vec![],
                })
            } else {
                Err(err).context("Failed to decode pixel data")
            }
        }
    }
}

pub fn pixel_statistics_from_decoded(decoded: &DecodedPixelData) -> Result<PixelStatistics> {
    let (values, mut shape) = pixel_values(decoded)?;
    // Normalize shape to [frames, samples, rows, cols] for reporting consistency.
    if shape.len() == 4 {
        let frames = shape[0];
        let rows = shape[1];
        let cols = shape[2];
        let samples = shape[3];
        shape = vec![frames, samples, rows, cols];
    }

    if values.is_empty() {
        return Ok(PixelStatistics {
            min: 0.0,
            max: 0.0,
            mean: 0.0,
            median: None,
            std_dev: 0.0,
            total_pixels: 0,
            shape,
        });
    }

    let mut min = f32::INFINITY;
    let mut max = f32::NEG_INFINITY;
    let mut sum = 0f64;

    for &v in &values {
        min = min.min(v);
        max = max.max(v);
        sum += v as f64;
    }

    let total_pixels = values.len();
    let mean = (sum / total_pixels as f64) as f32;

    let mut variance_sum = 0f64;
    for v in &values {
        let diff = *v as f64 - mean as f64;
        variance_sum += diff * diff;
    }
    let std_dev = (variance_sum / total_pixels as f64).sqrt() as f32;

    let median = {
        let mut sorted = values.clone();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let mid = sorted.len() / 2;
        if sorted.len() % 2 == 0 {
            Some((sorted[mid - 1] + sorted[mid]) / 2.0)
        } else {
            Some(sorted[mid])
        }
    };

    Ok(PixelStatistics {
        min,
        max,
        mean,
        median,
        std_dev,
        total_pixels,
        shape,
    })
}

/// Generate an intensity histogram for the pixel data.
pub fn histogram_for_file(input: &Path, bins: usize) -> Result<PixelHistogram> {
    let obj = open_file(input).context("Failed to open DICOM file")?;
    if let Ok(elem) = obj.element(tags::PIXEL_DATA) {
        if elem.value().length().0 == 0 {
            return Ok(PixelHistogram {
                bins: vec![],
                min: 0.0,
                max: 0.0,
            });
        }
    }

    match obj.decode_pixel_data() {
        Ok(decoded) => histogram_from_decoded(&decoded, bins),
        Err(err) => {
            let msg = format!("{err}");
            if msg.contains("Frame #0 is out of range") || msg.contains("no pixel data") {
                return Ok(PixelHistogram {
                    bins: vec![],
                    min: 0.0,
                    max: 0.0,
                });
            }
            Err(err).context("Failed to decode pixel data")
        }
    }
}

pub fn histogram_from_decoded(decoded: &DecodedPixelData, bins: usize) -> Result<PixelHistogram> {
    let (values, _shape) = pixel_values(decoded)?;

    if values.is_empty() {
        return Ok(PixelHistogram {
            bins: vec![],
            min: 0.0,
            max: 0.0,
        });
    }

    let mut min = f32::INFINITY;
    let mut max = f32::NEG_INFINITY;
    for &v in &values {
        min = min.min(v);
        max = max.max(v);
    }

    let bin_count = bins.max(1);
    let mut counts = vec![0u64; bin_count];
    let range = max - min;
    for &v in &values {
        let idx = if range == 0.0 {
            0
        } else {
            (((v - min) / range) * (bin_count as f32)).floor() as usize
        };
        let clamped = idx.min(bin_count - 1);
        counts[clamped] += 1;
    }

    Ok(PixelHistogram {
        bins: counts,
        min,
        max,
    })
}

/// Summarize pixel format information (bits, samples, VOI/LUT).
pub fn pixel_format_for_file(input: &Path) -> Result<PixelFormatSummary> {
    let obj = open_file(input).context("Failed to open DICOM file")?;
    let decoded = obj
        .decode_pixel_data()
        .context("Failed to decode pixel data")?;
    pixel_format_from_decoded(&decoded)
}

pub fn pixel_format_from_decoded(decoded: &DecodedPixelData) -> Result<PixelFormatSummary> {
    let rescale_all = decoded.rescale()?.to_vec();
    let window_all = decoded.window()?.map(|w| w.to_vec());
    let rescale = rescale_all.first().cloned();
    let window = window_all.as_ref().and_then(|w| w.first()).cloned();
    let pi = decoded.photometric_interpretation();
    let planar_config = if decoded.samples_per_pixel() > 1 {
        Some(decoded.planar_configuration())
    } else {
        None
    };
    let per_frame_voi = build_per_frame_voi(decoded, &rescale_all, window_all.as_deref());

    Ok(PixelFormatSummary {
        rows: decoded.rows(),
        columns: decoded.columns(),
        number_of_frames: decoded.number_of_frames(),
        samples_per_pixel: decoded.samples_per_pixel(),
        photometric_interpretation: format!("{:?}", pi),
        planar_configuration: planar_config.map(|p| format!("{:?}", p)),
        bits_allocated: decoded.bits_allocated(),
        bits_stored: decoded.bits_stored(),
        high_bit: decoded.high_bit(),
        pixel_representation: format!("{:?}", decoded.pixel_representation()),
        rescale_slope: rescale.map(|r| r.slope),
        rescale_intercept: rescale.map(|r| r.intercept),
        window_center: window.map(|w| w.center),
        window_width: window.map(|w| w.width),
        per_frame_voi,
    })
}

fn build_per_frame_voi(
    decoded: &DecodedPixelData,
    rescales: &[Rescale],
    windows: Option<&[WindowLevel]>,
) -> Option<Vec<FrameVoi>> {
    let frame_count = decoded.number_of_frames() as usize;
    let has_multiple_frames = frame_count > 1;
    let varying_rescale = rescales.len() > 1;
    let varying_window = windows.map(|w| w.len() > 1).unwrap_or(false);

    if !has_multiple_frames && !varying_rescale && !varying_window {
        return None;
    }

    let mut per_frame = Vec::with_capacity(frame_count.max(1));
    for idx in 0..frame_count {
        let rescale = rescales
            .get(idx)
            .or_else(|| rescales.first())
            .copied()
            .unwrap_or(Rescale {
                intercept: 0.0,
                slope: 1.0,
            });

        let window = windows
            .and_then(|w| w.get(idx).or_else(|| w.first()))
            .copied();

        per_frame.push(FrameVoi {
            frame_index: idx as u32,
            window_center: window.map(|w| w.center),
            window_width: window.map(|w| w.width),
            rescale_slope: Some(rescale.slope),
            rescale_intercept: Some(rescale.intercept),
        });
    }

    Some(per_frame)
}

fn pixel_values(decoded: &DecodedPixelData) -> Result<(Vec<f32>, Vec<usize>)> {
    // Apply modality LUT by default to reflect clinician-facing values.
    let options = ConvertOptions::new().with_modality_lut(ModalityLutOption::Default);
    let array = decoded.to_ndarray_with_options::<f32>(&options)?;
    let shape = array.shape().to_vec();
    let values = array.into_raw_vec();
    Ok((values, shape))
}

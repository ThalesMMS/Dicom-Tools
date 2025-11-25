//
// image.rs
// Dicom-Tools-rs
//
// Converts decoded DICOM pixel data into standard image formats with optional LUT/VOI handling and frame selection.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::{bail, Context, Result};
use dicom::object::open_file;
use dicom::pixeldata::PixelDecoder;
use dicom_pixeldata::{ConvertOptions, ModalityLutOption, VoiLutOption, WindowLevel};
use image::{DynamicImage, ImageFormat};
use std::io::Cursor;
use std::path::{Path, PathBuf};

/// Options controlling how pixel data is converted into a displayable image.
#[derive(Debug, Clone, Default)]
pub struct ImageExportOptions {
    pub frame: Option<u32>,
    pub window: Option<WindowLevel>,
    pub normalize: bool,
    pub disable_modality_lut: bool,
    pub disable_voi_lut: bool,
    pub force_8bit: bool,
    pub force_16bit: bool,
}

pub fn convert(
    input: &Path,
    output: Option<PathBuf>,
    format: &str,
    options: &ImageExportOptions,
) -> Result<()> {
    let obj = open_file(input).context("Failed to open DICOM file")?;

    // Decode pixel data (handles compression when features are enabled).
    // We do this once and reuse the decoded buffer for any frames requested.
    let decoded_image = obj
        .decode_pixel_data()
        .context("Failed to decode pixel data")?;
    let num_frames = decoded_image.number_of_frames();

    let base_output = output.unwrap_or_else(|| {
        let mut p = input.to_path_buf();
        p.set_extension(format);
        p
    });

    let frames: Vec<u32> = if let Some(frame) = options.frame {
        if frame >= num_frames {
            bail!(
                "Requested frame {} but file has {} frame(s)",
                frame,
                num_frames
            );
        }
        vec![frame]
    } else {
        (0..num_frames).collect()
    };

    let convert_options = build_convert_options(options);

    if frames.len() == 1 {
        let dynamic_image =
            decoded_image.to_dynamic_image_with_options(frames[0], &convert_options)?;
        dynamic_image
            .save(&base_output)
            .with_context(|| format!("Failed to save image to {:?}", base_output))?;
        println!("Image saved to: {:?} (frame {})", base_output, frames[0]);
        return Ok(());
    }

    // Multi-frame images are expanded into numbered files alongside the base output.
    println!("Multi-frame DICOM detected: {} frames.", num_frames);
    let parent = base_output.parent().unwrap_or_else(|| Path::new("."));
    let stem = base_output.file_stem().unwrap().to_string_lossy();

    for i in frames {
        let dynamic_image = decoded_image.to_dynamic_image_with_options(i, &convert_options)?;
        let frame_name = format!("{}_frame{:03}.{}", stem, i, format);
        let frame_path = parent.join(frame_name);

        dynamic_image
            .save(&frame_path)
            .with_context(|| format!("Failed to save image to {:?}", frame_path))?;
        println!("Saved frame {} to {:?}", i, frame_path);
    }

    Ok(())
}

pub fn first_frame_png_bytes(input: &Path) -> Result<Vec<u8>> {
    let obj = open_file(input)?;
    // Use the default conversion pipeline to render a thumbnail-friendly PNG.
    let decoded_image = obj.decode_pixel_data()?;
    let dynamic_image = decoded_image.to_dynamic_image(0)?;
    encode_image(&dynamic_image, ImageFormat::Png)
}

/// Decode a single frame without loading every frame into memory.
pub fn read_frame_lazy(input: &Path, frame: u32) -> Result<Vec<u8>> {
    let obj = open_file(input).context("Failed to open DICOM file")?;
    let decoded = obj
        .decode_pixel_data_frame(frame)
        .context("Failed to decode requested frame")?;
    Ok(decoded.data().to_vec())
}

fn encode_image(image: &DynamicImage, format: ImageFormat) -> Result<Vec<u8>> {
    let mut buffer = Vec::new();
    image.write_to(&mut Cursor::new(&mut buffer), format)?;
    Ok(buffer)
}

fn build_convert_options(options: &ImageExportOptions) -> ConvertOptions {
    // Start with default options and opt out of LUTs/VOI transforms depending on flags.
    let mut convert = ConvertOptions::new();

    if options.disable_modality_lut {
        convert = convert.with_modality_lut(ModalityLutOption::None);
    }

    if options.disable_voi_lut {
        convert = convert.with_voi_lut(VoiLutOption::Identity);
    } else if let Some(window) = &options.window {
        convert = convert.with_voi_lut(VoiLutOption::Custom(*window));
    } else if options.normalize {
        convert = convert.with_voi_lut(VoiLutOption::Normalize);
    }

    if options.force_16bit {
        convert = convert.force_16bit();
    } else if options.force_8bit {
        convert = convert.force_8bit();
    }

    convert
}

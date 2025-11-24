//
// metadata.rs
// Dicom-Tools-rs
//
// Extracts basic and detailed metadata from DICOM objects for CLI summaries and API responses.
//
// Thales Matheus Mendonça Santos - November 2025

use std::collections::BTreeMap;
use std::path::Path;

use anyhow::{Context, Result};
use dicom::core::Tag;
use dicom::object::{open_file, DefaultDicomObject};

use crate::dicom_access::ElementAccess;
use crate::models::{BasicMetadata, DetailedMetadata, PixelFormatSummary};
use crate::stats;

fn text_for_tag<T: ElementAccess>(obj: &T, tag: Tag) -> Option<String> {
    // Thin wrapper to keep tag lookups concise in the call sites.
    obj.element_str(tag)
}

fn uint_for_tag<T: ElementAccess>(obj: &T, tag: Tag) -> Option<u32> {
    // Numeric values come back as strings; ElementAccess handles the parsing.
    obj.element_u32(tag)
}

fn insert_if(map: &mut BTreeMap<String, String>, label: &str, value: Option<String>) {
    // Only materialize present values so the API stays clean of empty fields.
    if let Some(value) = value {
        map.insert(label.to_string(), value);
    }
}

pub fn extract_basic_metadata<T: ElementAccess>(obj: &T) -> BasicMetadata {
    // Pull the handful of fields most callers care about without heavy allocation.
    let patient_name = text_for_tag(obj, Tag(0x0010, 0x0010));
    let patient_id = text_for_tag(obj, Tag(0x0010, 0x0020));
    let study_date = text_for_tag(obj, Tag(0x0008, 0x0020));
    let modality = text_for_tag(obj, Tag(0x0008, 0x0060));
    let sop_class_uid = text_for_tag(obj, Tag(0x0008, 0x0016));
    let has_pixel_data = obj.has_element(Tag(0x7fe0, 0x0010));
    let transfer_syntax = obj.transfer_syntax();
    let rows = uint_for_tag(obj, Tag(0x0028, 0x0010));
    let columns = uint_for_tag(obj, Tag(0x0028, 0x0011));
    let number_of_frames = uint_for_tag(obj, Tag(0x0028, 0x0008));

    BasicMetadata {
        patient_name,
        patient_id,
        study_date,
        modality,
        sop_class_uid,
        has_pixel_data,
        transfer_syntax,
        rows,
        columns,
        number_of_frames,
    }
}

pub fn extract_detailed_metadata<T: ElementAccess>(obj: &T) -> DetailedMetadata {
    // Build categorized maps for easier rendering in APIs and the web UI.
    let mut patient = BTreeMap::new();
    insert_if(&mut patient, "Name", text_for_tag(obj, Tag(0x0010, 0x0010)));
    insert_if(&mut patient, "ID", text_for_tag(obj, Tag(0x0010, 0x0020)));
    insert_if(
        &mut patient,
        "Birth Date",
        text_for_tag(obj, Tag(0x0010, 0x0030)),
    );
    insert_if(&mut patient, "Sex", text_for_tag(obj, Tag(0x0010, 0x0040)));

    let mut study = BTreeMap::new();
    insert_if(&mut study, "Date", text_for_tag(obj, Tag(0x0008, 0x0020)));
    insert_if(&mut study, "Time", text_for_tag(obj, Tag(0x0008, 0x0030)));
    insert_if(
        &mut study,
        "Description",
        text_for_tag(obj, Tag(0x0008, 0x1030)),
    );
    insert_if(
        &mut study,
        "Accession Number",
        text_for_tag(obj, Tag(0x0008, 0x0050)),
    );

    let mut image = BTreeMap::new();
    insert_if(
        &mut image,
        "Modality",
        text_for_tag(obj, Tag(0x0008, 0x0060)),
    );
    insert_if(&mut image, "Rows", text_for_tag(obj, Tag(0x0028, 0x0010)));
    insert_if(
        &mut image,
        "Columns",
        text_for_tag(obj, Tag(0x0028, 0x0011)),
    );
    insert_if(
        &mut image,
        "Pixel Representation",
        text_for_tag(obj, Tag(0x0028, 0x0103)),
    );
    insert_if(
        &mut image,
        "Photometric Interpretation",
        text_for_tag(obj, Tag(0x0028, 0x0004)),
    );
    insert_if(
        &mut image,
        "Number of Frames",
        text_for_tag(obj, Tag(0x0028, 0x0008)),
    );

    let mut misc = BTreeMap::new();
    insert_if(
        &mut misc,
        "SOP Class UID",
        text_for_tag(obj, Tag(0x0008, 0x0016)),
    );
    insert_if(
        &mut misc,
        "SOP Instance UID",
        text_for_tag(obj, Tag(0x0008, 0x0018)),
    );
    if let Some(ts) = obj.transfer_syntax() {
        insert_if(&mut misc, "Transfer Syntax", Some(ts));
    }

    DetailedMetadata {
        patient,
        study,
        image,
        misc,
    }
}

pub fn read_basic_metadata(path: &Path) -> Result<BasicMetadata> {
    let obj: DefaultDicomObject = open_file(path).context("Falha ao abrir arquivo DICOM")?;
    Ok(extract_basic_metadata(&obj))
}

pub fn read_detailed_metadata(path: &Path) -> Result<DetailedMetadata> {
    let obj: DefaultDicomObject = open_file(path).context("Falha ao abrir arquivo DICOM")?;
    Ok(extract_detailed_metadata(&obj))
}

pub fn print_info(path: &Path, verbose: bool) -> Result<()> {
    let obj: DefaultDicomObject = open_file(path).context("Falha ao abrir arquivo DICOM")?;
    let basic = extract_basic_metadata(&obj);
    let pixel_format = if basic.has_pixel_data {
        stats::pixel_format_for_file(path).ok()
    } else {
        None
    };

    println!("{}", "=".repeat(80));
    println!("DICOM File Information: {:?}", path.file_name().unwrap());
    println!("{}", "=".repeat(80));

    println!("PATIENT");
    println!("  Name: {}", basic.patient_name.as_deref().unwrap_or("N/A"));
    println!("  ID:   {}", basic.patient_id.as_deref().unwrap_or("N/A"));

    println!("\nSTUDY");
    println!("  Date: {}", basic.study_date.as_deref().unwrap_or("N/A"));
    println!(
        "  SOP Class: {}",
        basic.sop_class_uid.as_deref().unwrap_or("N/A")
    );
    println!(
        "  Transfer Syntax: {}",
        basic
            .transfer_syntax
            .as_deref()
            .unwrap_or("Unknown (in-memory)")
    );

    println!("\nIMAGE");
    println!("  Modality: {}", basic.modality.as_deref().unwrap_or("N/A"));
    println!(
        "  Pixel Data: {}",
        if basic.has_pixel_data {
            "present"
        } else {
            "absent"
        }
    );
    println!(
        "  Dimensions: {} x {}{}",
        basic
            .rows
            .map(|r| r.to_string())
            .unwrap_or_else(|| "?".into()),
        basic
            .columns
            .map(|c| c.to_string())
            .unwrap_or_else(|| "?".into()),
        basic
            .number_of_frames
            .map(|f| format!(" ({} frame{})", f, if f == 1 { "" } else { "s" }))
            .unwrap_or_default()
    );

    if let Some(format) = &pixel_format {
        print_pixel_format(format);
    }

    if verbose {
        // Verbose mode dumps every element header/value tuple for quick inspection.
        println!("\nALL TAGS (Verbose):");
        for element in obj.iter() {
            println!("  {} : {:?}", element.header().tag, element.value());
        }
    }

    Ok(())
}

fn print_pixel_format(format: &PixelFormatSummary) {
    println!("  Samples: {}", format.samples_per_pixel);
    println!("  Photometric: {}", format.photometric_interpretation);
    if let Some(planar) = &format.planar_configuration {
        println!("  Planar Configuration: {}", planar);
    }
    println!(
        "  Bits: stored={} allocated={} high_bit={}",
        format.bits_stored, format.bits_allocated, format.high_bit
    );
    println!("  Pixel Representation: {}", format.pixel_representation);
    if let (Some(center), Some(width)) = (format.window_center, format.window_width) {
        println!("  Window: center={} width={}", center, width);
    }
    if let (Some(slope), Some(intercept)) = (format.rescale_slope, format.rescale_intercept) {
        println!("  Rescale: slope={} intercept={}", slope, intercept);
    }
}

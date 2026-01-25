//
// validate.rs
// Dicom-Tools-rs
//
// Validates critical DICOM attributes and pixel presence, emitting summaries for CLI and API clients.
//
// Thales Matheus Mendonça Santos - November 2025

use std::path::Path;

use anyhow::{Context, Result};
use dicom::core::Tag;
use dicom::object::open_file;
use serde::Serialize;

use crate::dicom_access::ElementAccess;
use crate::models::ValidationSummary;

#[derive(Debug, Clone, Serialize)]
pub struct ValidationReport {
    pub valid: bool,
    pub missing_tags: Vec<String>,
    pub has_pixel_data: bool,
}

/// Validates a DICOM object in memory.
pub fn validate_obj<T: ElementAccess>(obj: &T) -> ValidationReport {
    // Core attributes pulled from PS3.3 C.7.2.1 plus pixel presence.
    let required_tags = vec![
        (Tag(0x0008, 0x0016), "SOP Class UID"),
        (Tag(0x0008, 0x0018), "SOP Instance UID"),
        (Tag(0x0010, 0x0010), "Patient Name"),
        (Tag(0x0010, 0x0020), "Patient ID"),
        (Tag(0x0008, 0x0020), "Study Date"),
        (Tag(0x0008, 0x0060), "Modality"),
    ];

    let mut missing_tags = Vec::new();

    for (tag, name) in required_tags {
        if !obj.has_element(tag) {
            missing_tags.push(format!("{} ({})", name, tag));
        }
    }

    let pixel_data_tag = Tag(0x7fe0, 0x0010);
    let has_pixel_data = obj.has_element(pixel_data_tag);

    ValidationReport {
        valid: missing_tags.is_empty(),
        missing_tags,
        has_pixel_data,
    }
}

pub fn as_summary(report: &ValidationReport) -> ValidationSummary {
    ValidationSummary {
        valid: report.valid,
        missing_tags: report.missing_tags.clone(),
        has_pixel_data: report.has_pixel_data,
    }
}

/// Validates if a file can be parsed as DICOM and prints a detailed summary.
pub fn check_file(path: &Path) -> Result<()> {
    println!("Validating: {:?}", path);
    let obj = open_file(path).context("Failed to open/parse DICOM file")?;
    let meta = obj.meta();

    // Echo key meta info before running attribute-level checks.
    println!("[OK] File Structure Parsed");
    println!("[OK] Transfer Syntax: {}", meta.transfer_syntax());
    println!(
        "[OK] Media Storage SOP Class: {}",
        meta.media_storage_sop_class_uid
    );

    let report = validate_obj(&obj);

    if report.has_pixel_data {
        println!("[OK] Pixel Data present");
    } else {
        println!("[WARN] No Pixel Data found");
    }

    if report.valid {
        println!("\nResult: VALID (All critical attributes found)");
    } else {
        println!(
            "\nResult: INVALID ({} critical attributes missing)",
            report.missing_tags.len()
        );
        for missing in report.missing_tags {
            println!("[MISSING] {}", missing);
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use dicom::core::{DataElement, PrimitiveValue, VR};
    use dicom::object::InMemDicomObject;

    #[test]
    fn test_validate_empty_object() {
        let obj = InMemDicomObject::new_empty();
        let report = validate_obj(&obj);
        assert!(!report.valid);
        assert!(report.missing_tags.len() >= 6);
        assert!(!report.has_pixel_data);
    }

    #[test]
    fn test_validate_valid_object() {
        let mut obj = InMemDicomObject::new_empty();

        obj.put(DataElement::new(
            Tag(0x0008, 0x0016),
            VR::UI,
            PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.2"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0018),
            VR::UI,
            PrimitiveValue::from("1.2.3.4.5"),
        ));
        obj.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("Doe^John"),
        ));
        obj.put(DataElement::new(
            Tag(0x0010, 0x0020),
            VR::LO,
            PrimitiveValue::from("12345"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0020),
            VR::DA,
            PrimitiveValue::from("20230101"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0060),
            VR::CS,
            PrimitiveValue::from("CT"),
        ));

        let report = validate_obj(&obj);
        assert!(
            report.valid,
            "Object should be valid, missing: {:?}",
            report.missing_tags
        );
        assert!(!report.has_pixel_data);
    }
}

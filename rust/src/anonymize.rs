//
// anonymize.rs
// Dicom-Tools-rs
//
// Implements deterministic anonymization of DICOM attributes, hashing identifiers and scrubbing PII fields.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::Result;
use dicom::core::header::Header;
use dicom::core::value::PrimitiveValue;
use dicom::core::{DataElement, Tag, VR};
use dicom::object::{open_file, InMemDicomObject};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

const TAGS_TO_REMOVE: &[Tag] = &[
    Tag(0x0008, 0x0050), // AccessionNumber
    Tag(0x0010, 0x0021), // IssuerOfPatientID
    Tag(0x0010, 0x1000), // OtherPatientIDs
    Tag(0x0010, 0x1001), // OtherPatientNames
    Tag(0x0010, 0x1005), // PatientBirthName
    Tag(0x0008, 0x0096), // ReferringPhysicianIdentificationSequence
    Tag(0x0032, 0x1032), // RequestingPhysician
    Tag(0x0032, 0x1033), // RequestingService
    Tag(0x0040, 0x0275), // RequestAttributesSequence
    Tag(0x0040, 0x0007), // ScheduledProcedureStepDescription
    Tag(0x0040, 0x0254), // PerformedProcedureStepDescription
];

const TAGS_TO_EMPTY: &[Tag] = &[
    Tag(0x0010, 0x1040), // PatientAddress
    Tag(0x0010, 0x2154), // PatientTelephoneNumbers
    Tag(0x0010, 0x1060), // PatientMotherBirthName
    Tag(0x0010, 0x0040), // PatientSex
    Tag(0x0010, 0x1010), // PatientAge
    Tag(0x0010, 0x1030), // PatientWeight
    Tag(0x0010, 0x1020), // PatientSize
    Tag(0x0010, 0x1080), // MilitaryRank
    Tag(0x0010, 0x2160), // EthnicGroup
    Tag(0x0010, 0x2180), // Occupation
    Tag(0x0010, 0x21B0), // AdditionalPatientHistory
    Tag(0x0010, 0x4000), // PatientComments
    Tag(0x0010, 0x2297), // ResponsiblePerson
    Tag(0x0010, 0x2299), // ResponsibleOrganization
    Tag(0x0008, 0x0092), // ReferringPhysicianAddress
    Tag(0x0008, 0x0094), // ReferringPhysicianTelephoneNumbers
    Tag(0x0008, 0x0081), // InstitutionAddress
    Tag(0x0008, 0x1040), // InstitutionalDepartmentName
    Tag(0x0008, 0x1010), // StationName
];

const TAGS_TO_ANONYMIZE: &[Tag] = &[
    Tag(0x0008, 0x0080), // InstitutionName
    Tag(0x0008, 0x1048), // PhysiciansOfRecord
    Tag(0x0008, 0x1050), // PerformingPhysicianName
    Tag(0x0008, 0x1070), // OperatorsName
];

/// Generate a reproducible anonymized identifier by hashing the original value and trimming it.
fn generate_hash(original: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(original.as_bytes());
    let result = hasher.finalize();
    hex::encode(&result)[..16].to_uppercase()
}

fn is_private_tag(tag: Tag) -> bool {
    tag.group() % 2 == 1
}

fn replace_if_present(obj: &mut InMemDicomObject, tag: Tag, value: &str) {
    if let Ok(vr) = obj.element(tag).map(|elem| elem.vr()) {
        obj.put(DataElement::new(tag, vr, PrimitiveValue::from(value)));
    }
}

pub fn anonymize_obj(obj: &mut InMemDicomObject) -> Result<()> {
    // 1. Get original ID to derive a hash.
    //    We avoid randomization so repeated runs on the same input remain stable.
    let patient_id_tag = Tag(0x0010, 0x0020);
    let original_id = obj
        .element(patient_id_tag)
        .ok()
        .and_then(|e| e.to_str().ok())
        .unwrap_or("UNKNOWN".into());

    let anon_id = format!("ANON_{}", generate_hash(&original_id));

    // 2. Collect tags that need replacement based on VR
    //    Walking once lets us avoid borrowing issues while editing later.
    let mut replacements = Vec::new();

    for elem in obj.iter() {
        let tag = elem.tag();
        let vr = elem.vr();

        // Skip PatientID (handled explicitly)
        if tag == patient_id_tag {
            continue;
        }

        match vr {
            VR::PN => {
                if tag == Tag(0x0010, 0x0010) {
                    replacements.push((tag, vr, "ANONYMOUS^PATIENT".to_string()));
                } else {
                    replacements.push((tag, vr, "ANONYMIZED".to_string()));
                }
            }
            VR::DA => {
                replacements.push((tag, vr, "19010101".to_string()));
            }
            VR::TM => {
                replacements.push((tag, vr, "000000".to_string()));
            }
            VR::DT => {
                replacements.push((tag, vr, "19010101000000".to_string()));
            }
            _ => {}
        }
    }

    // 3. Apply generic replacements.
    for (tag, vr, val) in replacements {
        obj.put(DataElement::new(tag, vr, PrimitiveValue::from(val)));
    }

    // 4. Apply specific PatientID override with the derived hash.
    obj.put(DataElement::new(
        patient_id_tag,
        VR::LO,
        PrimitiveValue::from(anon_id),
    ));

    // 5. Apply explicit PHI policy for common non-PN identifiers and site metadata.
    for &tag in TAGS_TO_REMOVE {
        obj.remove_element(tag);
    }

    for &tag in TAGS_TO_EMPTY {
        replace_if_present(obj, tag, "");
    }

    for &tag in TAGS_TO_ANONYMIZE {
        replace_if_present(obj, tag, "ANONYMIZED");
    }

    // 6. Remove private tags after collecting them to avoid mutating during iteration.
    let private_tags: Vec<_> = obj
        .iter()
        .map(|elem| elem.tag())
        .filter(|tag| is_private_tag(*tag))
        .collect();

    for tag in private_tags {
        obj.remove_element(tag);
    }

    Ok(())
}

pub fn process_file(input: &Path, output: Option<PathBuf>) -> Result<()> {
    let mut obj = open_file(input)?;

    anonymize_obj(&mut obj)?;

    // 5. Save file
    let output_path = output.unwrap_or_else(|| {
        let mut p = input.to_path_buf();
        let stem = p.file_stem().unwrap().to_str().unwrap();
        p.set_file_name(format!("{}_anon.dcm", stem));
        p
    });

    obj.write_to_file(&output_path)?;
    println!("Anonymized file saved to: {:?}", output_path);

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use dicom::core::DataElement;
    use dicom::object::InMemDicomObject;

    #[test]
    fn test_anonymization() {
        let mut obj = InMemDicomObject::new_empty();

        // Setup sensitive data
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
            Tag(0x0010, 0x0030),
            VR::DA,
            PrimitiveValue::from("19800101"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0090),
            VR::PN,
            PrimitiveValue::from("Dr. House"),
        ));

        anonymize_obj(&mut obj).unwrap();

        // Verify Patient Name
        let name = obj.element(Tag(0x0010, 0x0010)).unwrap().to_str().unwrap();
        assert_eq!(name, "ANONYMOUS^PATIENT");

        // Verify Patient ID (hashed)
        let pid = obj.element(Tag(0x0010, 0x0020)).unwrap().to_str().unwrap();
        assert!(pid.starts_with("ANON_"));
        assert_ne!(pid, "12345");

        // Verify Date (DA)
        let dob = obj.element(Tag(0x0010, 0x0030)).unwrap().to_str().unwrap();
        assert_eq!(dob, "19010101");

        // Verify Other Physician Name (PN)
        let doctor = obj.element(Tag(0x0008, 0x0090)).unwrap().to_str().unwrap();
        assert_eq!(doctor, "ANONYMIZED");
    }

    #[test]
    fn anonymization_scrubs_explicit_phi_tags_and_private_tags() {
        let mut obj = InMemDicomObject::new_empty();

        obj.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("Doe^Jane"),
        ));
        obj.put(DataElement::new(
            Tag(0x0010, 0x0020),
            VR::LO,
            PrimitiveValue::from("MRN-12345"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0050),
            VR::SH,
            PrimitiveValue::from("ACC-9988"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0080),
            VR::LO,
            PrimitiveValue::from("Saint Mary's Hospital"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x1010),
            VR::SH,
            PrimitiveValue::from("CT-ROOM-7"),
        ));
        obj.put(DataElement::new(
            Tag(0x0010, 0x1040),
            VR::LO,
            PrimitiveValue::from("123 Main St"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0090),
            VR::PN,
            PrimitiveValue::from("Doctor^Who"),
        ));
        obj.put(DataElement::new(
            Tag(0x0011, 0x1010),
            VR::LO,
            PrimitiveValue::from("PRIVATE-PHI"),
        ));

        anonymize_obj(&mut obj).unwrap();

        assert_eq!(
            obj.element(Tag(0x0010, 0x0010)).unwrap().to_str().unwrap(),
            "ANONYMOUS^PATIENT"
        );
        assert_ne!(
            obj.element(Tag(0x0010, 0x0020)).unwrap().to_str().unwrap(),
            "MRN-12345"
        );
        assert!(obj.element(Tag(0x0008, 0x0050)).is_err());
        assert_eq!(
            obj.element(Tag(0x0008, 0x0080)).unwrap().to_str().unwrap(),
            "ANONYMIZED"
        );
        assert_eq!(
            obj.element(Tag(0x0008, 0x1010)).unwrap().to_str().unwrap(),
            ""
        );
        assert_eq!(
            obj.element(Tag(0x0010, 0x1040)).unwrap().to_str().unwrap(),
            ""
        );
        assert_eq!(
            obj.element(Tag(0x0008, 0x0090)).unwrap().to_str().unwrap(),
            "ANONYMIZED"
        );
        assert!(obj.element(Tag(0x0011, 0x1010)).is_err());
    }
}

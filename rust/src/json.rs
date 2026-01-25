//
// json.rs
// Dicom-Tools-rs
//
// Handles round-tripping DICOM objects to and from JSON representations for inspection or transformation.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::{Context, Result};
use dicom::object::{open_file, InMemDicomObject};
// Re-export StandardDataDictionary from dicom crate (v0.7 uses dicom_dictionary_std v0.7 internally)
// We can access it via dicom::dictionary_std or similar if exposed,
// or just rely on generic inference if possible.
// In dicom 0.7, `dicom::object::StandardDataDictionary` might be available.
use dicom::object::FileMetaTableBuilder;
use dicom::object::StandardDataDictionary;
use dicom_json::{from_value, DicomJson};
use serde_json::Value;
use std::fs::File;
use std::path::Path;

/// Convert a DICOM file to JSON and print it to stdout.
pub fn to_json(input: &Path, output: Option<&Path>) -> Result<()> {
    // Delegate to the pure function so behavior is consistent across CLI and API.
    let json_string = to_json_string(input)?;

    match output {
        Some(path) => {
            std::fs::write(path, json_string).context("Failed to write JSON to file")?;
            println!("JSON saved to {:?}", path);
        }
        None => {
            println!("{}", json_string);
        }
    }

    Ok(())
}

/// Convert a DICOM file into a pretty JSON string without touching the filesystem.
pub fn to_json_string(input: &Path) -> Result<String> {
    let obj = open_file(input).context("Failed to open DICOM file")?;

    // The in-memory object implements serde-friendly conversions via dicom-json.
    let inner_obj: &InMemDicomObject<StandardDataDictionary> = &*obj;
    let json_obj = DicomJson::from(inner_obj);

    let json_string =
        serde_json::to_string_pretty(&json_obj).context("Failed to serialize to JSON")?;
    Ok(json_string)
}

/// Create a DICOM file from a JSON source.
pub fn from_json(input: &Path, output: &Path) -> Result<()> {
    let file = File::open(input).context("Failed to open JSON file")?;
    let json_val: Value = serde_json::from_reader(file).context("Failed to parse JSON")?;

    // Build the in-memory object first so we can attach file meta afterwards.
    let obj: InMemDicomObject<StandardDataDictionary> =
        from_value(json_val).context("Failed to convert JSON to DICOM object")?;

    use dicom::object::FileDicomObject;

    let file_meta = FileMetaTableBuilder::new()
        .transfer_syntax(dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .build()?;

    let mut file_obj =
        FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary::default(), file_meta);

    // Copy elements into the file object in insertion order.
    for elem in obj {
        file_obj.put(elem);
    }

    file_obj
        .write_to_file(output)
        .context("Failed to write DICOM file")?;

    println!("DICOM saved to {:?}", output);

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
    use dicom::object::InMemDicomObject;

    #[test]
    fn test_json_roundtrip() {
        let mut obj = InMemDicomObject::new_empty();
        obj.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("Test^Patient"),
        ));
        obj.put(DataElement::new(
            Tag(0x0010, 0x0020),
            VR::LO,
            PrimitiveValue::from("12345"),
        ));

        let json_obj = DicomJson::from(&obj);
        let json_val = serde_json::to_value(&json_obj).unwrap();

        let restored: InMemDicomObject<StandardDataDictionary> =
            from_value(json_val).expect("Deserialization failed");

        let name = restored
            .element(Tag(0x0010, 0x0010))
            .unwrap()
            .to_str()
            .unwrap();
        assert_eq!(name, "Test^Patient");
    }
}

//
// dump.rs
// Dicom-Tools-rs
//
// Renders a human-readable dump of a DICOM dataset, including sequences, with configurable depth and value previews.
//
// Thales Matheus Mendonça Santos - November 2025

use std::fmt::Write;
use std::path::Path;

use anyhow::{Context, Result};
use dicom::core::dictionary::DataDictionary;
use dicom::core::value::Value;
use dicom::core::{PrimitiveValue, Tag};
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{open_file, InMemDicomObject};

/// Print a textual dump of all elements in the file, resolving names via the standard dictionary.
pub fn dump_file(path: &Path, max_depth: usize, max_value_len: usize) -> Result<()> {
    let output = dump_to_string(path, max_depth, max_value_len)?;
    println!("{output}");
    Ok(())
}

pub fn dump_to_string(path: &Path, max_depth: usize, max_value_len: usize) -> Result<String> {
    // Loading and dumping are separated so the output can be reused in tests or APIs.
    let obj = open_file(path).context("Failed to open DICOM file")?;
    let mut out = String::new();
    dump_object(&obj, 0, max_depth, max_value_len, &mut out);
    Ok(out)
}

/// Render the entire dataset as standard DICOM JSON (lossless, includes sequences and pixel data).
pub fn dump_to_json(path: &Path) -> Result<String> {
    crate::json::to_json_string(path).context("Failed to render DICOM JSON")
}

fn dump_object(
    obj: &InMemDicomObject<StandardDataDictionary>,
    depth: usize,
    max_depth: usize,
    max_value_len: usize,
    out: &mut String,
) {
    for elem in obj.iter() {
        // Collect all metadata needed to render the line.
        let tag = elem.header().tag;
        let vr = elem.header().vr;
        let name = tag_name(tag);
        let indent = "  ".repeat(depth);

        match elem.value() {
            Value::Primitive(p) => {
                // Primitive values can be long; we surface a preview only.
                let preview = preview_primitive(p, max_value_len);
                let _ = writeln!(
                    out,
                    "{}{} {} {} {}",
                    indent,
                    format_tag(tag),
                    name,
                    vr,
                    preview
                );
            }
            Value::Sequence(seq) => {
                // For sequences, print the container then recurse into items (if allowed by depth).
                let _ = writeln!(
                    out,
                    "{}{} {} {} [sequence: {} item(s)]",
                    indent,
                    format_tag(tag),
                    name,
                    vr,
                    seq.items().len()
                );
                if depth < max_depth {
                    for (idx, item) in seq.items().iter().enumerate() {
                        let _ = writeln!(out, "{}  Item {}", indent, idx + 1);
                        dump_object(item, depth + 2, max_depth, max_value_len, out);
                    }
                }
            }
            Value::PixelSequence(p) => {
                // Encapsulated pixel data is summarized to avoid massive output.
                let _ = writeln!(
                    out,
                    "{}{} {} {} [encapsulated: {} fragment(s)]",
                    indent,
                    format_tag(tag),
                    name,
                    vr,
                    p.fragments().len()
                );
            }
        }
    }
}

fn preview_primitive(value: &PrimitiveValue, max_value_len: usize) -> String {
    let text = value.to_str();
    if !text.is_empty() {
        return truncate(&text, max_value_len);
    }

    let bytes = value.to_bytes();
    format!("{} bytes", bytes.len())
}

fn truncate(input: &str, limit: usize) -> String {
    if input.len() <= limit {
        input.to_string()
    } else {
        let mut truncated = input[..limit].to_string();
        truncated.push('…');
        truncated
    }
}

fn format_tag(tag: Tag) -> String {
    format!("({:04X},{:04X})", tag.group(), tag.element())
}

fn tag_name(tag: Tag) -> String {
    StandardDataDictionary::default()
        .by_tag(tag)
        .map(|e| e.alias.to_string())
        .unwrap_or_else(|| "UnknownTag".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use dicom::core::{DataElement, PrimitiveValue, VR};
    use dicom::dictionary_std::StandardDataDictionary;
    use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
    use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
    use tempfile::{tempdir, TempDir};

    fn sample_file() -> (TempDir, std::path::PathBuf) {
        let dir = tempdir().expect("tempdir");
        let path = dir.path().join("dump.dcm");

        let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        obj.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("Dump^Patient"),
        ));
        obj.put(DataElement::new(
            Tag(0x7FE0, 0x0010),
            VR::OB,
            PrimitiveValue::from(vec![1_u8, 2, 3, 4]),
        ));

        let meta = FileMetaTableBuilder::new()
            .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
            .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
            .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.9.2")
            .build()
            .expect("meta");

        let mut file_obj =
            FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
        for elem in obj {
            file_obj.put(elem);
        }
        file_obj.write_to_file(&path).expect("write dicom");

        (dir, path)
    }

    #[test]
    fn truncate_limits_preview() {
        let preview = truncate("ABCDEFGHIJ", 5);
        assert_eq!(preview, "ABCDE…");
    }

    #[test]
    fn dump_to_string_includes_tag_name_and_value() {
        let (_dir, path) = sample_file();
        let out = dump_to_string(&path, 2, 16).expect("dump");
        assert!(out.contains("(0010,0010)"));
        assert!(out.contains("Dump^Patient"));
    }
}

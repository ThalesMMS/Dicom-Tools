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

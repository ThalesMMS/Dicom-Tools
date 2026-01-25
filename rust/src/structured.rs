//
// structured.rs
// Dicom-Tools-rs
//
// Utilities for traversing deeply nested DICOM datasets (e.g., SR Content Sequences) using path segments.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::{Context, Result};
use dicom::core::value::Value;
use dicom::core::Tag;
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{open_file, DefaultDicomObject, InMemDicomObject};
use std::path::Path;

/// One hop in a navigation path. When `item_index` is provided, the tag must be a sequence.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PathSegment {
    pub tag: Tag,
    pub item_index: Option<usize>,
}

impl PathSegment {
    /// Navigate to a non-sequence element.
    pub fn element(tag: Tag) -> Self {
        Self {
            tag,
            item_index: None,
        }
    }

    /// Navigate into the `item_index`-th item of a sequence.
    pub fn item(tag: Tag, item_index: usize) -> Self {
        Self {
            tag,
            item_index: Some(item_index),
        }
    }
}

/// Resolve a navigation path within an object, returning a trimmed string value when present.
pub fn value_at_path(obj: &DefaultDicomObject, path: &[PathSegment]) -> Option<String> {
    if path.is_empty() {
        return None;
    }

    let mut current_item: Option<&InMemDicomObject<StandardDataDictionary>> = None;

    for (idx, segment) in path.iter().enumerate() {
        let element = match current_item {
            Some(item) => item.element(segment.tag).ok()?,
            None => obj.element(segment.tag).ok()?,
        };

        if let Some(item_index) = segment.item_index {
            match element.value() {
                Value::Sequence(seq) => {
                    current_item = seq.items().get(item_index);
                    if current_item.is_none() {
                        return None;
                    }
                }
                _ => return None,
            }
            continue;
        }

        let is_last = idx == path.len() - 1;
        if is_last {
            if let Ok(value) = element.to_str() {
                return Some(value.trim().to_string());
            }
            // Fallback to raw bytes when a string view is not available.
            if let Ok(bytes) = element.to_bytes() {
                return Some(format!("{:?}", bytes));
            }
            return None;
        }

        // If there is more path ahead, default to the first item of a sequence (common in SR trees).
        match element.value() {
            Value::Sequence(seq) => {
                current_item = seq.items().first();
                if current_item.is_none() {
                    return None;
                }
            }
            _ => return None,
        }
    }

    None
}

/// Open a file and resolve the navigation path within it.
pub fn value_at_path_from_file(path: &Path, segments: &[PathSegment]) -> Result<Option<String>> {
    let obj = open_file(path).context("Failed to open DICOM file")?;
    Ok(value_at_path(&obj, segments))
}

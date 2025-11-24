//
// dicom_access.rs
// Dicom-Tools-rs
//
// Provides a small trait to pull typed values from different DICOM object representations uniformly.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::Tag;
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::{DefaultDicomObject, InMemDicomObject};

/// Small helper trait to pull string values from different DICOM object shapes.
pub trait ElementAccess {
    fn element_str(&self, tag: Tag) -> Option<String>;
    fn element_u32(&self, tag: Tag) -> Option<u32>;
    fn has_element(&self, tag: Tag) -> bool;
    fn transfer_syntax(&self) -> Option<String>;
}

impl ElementAccess for DefaultDicomObject {
    fn element_str(&self, tag: Tag) -> Option<String> {
        // Many tags are optional; convert missing values into clean Option<String>.
        self.element(tag)
            .ok()
            .and_then(|e| e.to_str().ok())
            .map(|s| s.into_owned())
    }

    fn element_u32(&self, tag: Tag) -> Option<u32> {
        // Numeric tags are stored as strings; parse but tolerate errors quietly.
        self.element(tag)
            .ok()
            .and_then(|e| e.to_str().ok())
            .and_then(|s| s.into_owned().trim().parse::<u32>().ok())
    }

    fn has_element(&self, tag: Tag) -> bool {
        self.element(tag).is_ok()
    }

    fn transfer_syntax(&self) -> Option<String> {
        Some(self.meta().transfer_syntax().to_string())
    }
}

impl ElementAccess for InMemDicomObject<StandardDataDictionary> {
    fn element_str(&self, tag: Tag) -> Option<String> {
        // Same implementation as DefaultDicomObject but for the in-memory type.
        self.element(tag)
            .ok()
            .and_then(|e| e.to_str().ok())
            .map(|s| s.into_owned())
    }

    fn element_u32(&self, tag: Tag) -> Option<u32> {
        // Numeric tags are stored as strings; parse but tolerate errors quietly.
        self.element(tag)
            .ok()
            .and_then(|e| e.to_str().ok())
            .and_then(|s| s.into_owned().trim().parse::<u32>().ok())
    }

    fn has_element(&self, tag: Tag) -> bool {
        self.element(tag).is_ok()
    }

    fn transfer_syntax(&self) -> Option<String> {
        None
    }
}

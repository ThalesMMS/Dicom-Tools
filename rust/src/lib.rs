//
// lib.rs
// Dicom-Tools-rs
//
// Exposes the crate's modules and re-exports the CLI entry point for both binary and library consumers.
//
// Thales Matheus Mendonça Santos - November 2025

// Public surface of the library: each module mirrors a CLI verb or shared utility.
pub mod anonymize;
pub mod batch;
pub mod cli;
pub mod dicom_access;
pub mod dump;
pub mod functional_groups;
pub mod image;
pub mod json;
pub mod metadata;
pub mod models;
pub mod scu;
pub mod structured;
pub mod stats;
pub mod storage;
pub mod transcode;
pub mod validate;
pub mod web;

pub use cli::{run as run_cli, Cli, Commands};

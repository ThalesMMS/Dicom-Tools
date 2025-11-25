//
// cli_integration.rs
// Dicom-Tools-rs
//
// Light end-to-end smoke tests for the CLI commands.
//
// Thales Matheus Mendonça Santos - November 2025

mod support;

use assert_cmd::Command;
use predicates::str::contains;
use support::write_secondary_capture;
use tempfile::tempdir;

#[test]
fn cli_info_succeeds_on_sample_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("cli_info.dcm");
    write_secondary_capture(&path, "CLI^Patient");

    Command::cargo_bin("dicom-tools")
        .expect("bin")
        .args(["info", path.to_str().unwrap()])
        .assert()
        .success()
        .stdout(contains("Name: CLI^Patient"));
}

#[test]
fn cli_histogram_rejects_zero_bins() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("cli_hist.dcm");
    write_secondary_capture(&path, "CLI^Histogram");

    Command::cargo_bin("dicom-tools")
        .expect("bin")
        .args([
            "histogram",
            path.to_str().unwrap(),
            "--bins",
            "0",
        ])
        .assert()
        .failure();
}

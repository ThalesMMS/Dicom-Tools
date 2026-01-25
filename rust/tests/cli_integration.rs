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

#[test]
fn cli_stats_prints_total_pixels() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("cli_stats.dcm");
    write_secondary_capture(&path, "CLI^Stats");

    Command::cargo_bin("dicom-tools")
        .expect("bin")
        .args(["stats", path.to_str().unwrap()])
        .assert()
        .success()
        .stdout(contains("Total Pixels"));
}

#[test]
fn cli_validate_accepts_minimal_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("cli_validate.dcm");
    write_secondary_capture(&path, "CLI^Validate");

    Command::cargo_bin("dicom-tools")
        .expect("bin")
        .args(["validate", path.to_str().unwrap()])
        .assert()
        .success();
}

#[test]
fn cli_transcode_creates_output_file() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("cli_transcode.dcm");
    write_secondary_capture(&path, "CLI^Transcode");
    let output = dir.path().join("cli_transcoded.dcm");

    Command::cargo_bin("dicom-tools")
        .expect("bin")
        .args([
            "transcode",
            path.to_str().unwrap(),
            "--output",
            output.to_str().unwrap(),
            "--transfer-syntax",
            "implicit-vr-little-endian",
        ])
        .assert()
        .success();

    assert!(output.exists(), "transcoded file missing");
}

#[test]
fn cli_anonymize_changes_patient_name() {
    use dicom::object::open_file;
    use dicom::core::Tag;

    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("cli_anon.dcm");
    write_secondary_capture(&path, "CLI^Anon");
    let output = dir.path().join("cli_anon_out.dcm");

    Command::cargo_bin("dicom-tools")
        .expect("bin")
        .args([
            "anonymize",
            path.to_str().unwrap(),
            "--output",
            output.to_str().unwrap(),
        ])
        .assert()
        .success();

    let obj = open_file(&output).expect("open anon output");
    let name = obj.element(Tag(0x0010, 0x0010)).unwrap().to_str().unwrap();
    assert_ne!(name, "CLI^Anon");
}

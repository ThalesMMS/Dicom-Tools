//
// transfer_syntaxes.rs
// Dicom-Tools-rs
//
// Attempts to exercise newer transfer syntaxes (JPEG-LS, HTJ2K, JPEG-XL) via dicom-pixeldata.
// When codecs are unavailable, the tests assert that errors clearly surface unsupported syntaxes.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::Result;
use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::{open_file, FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom_tools::stats;
use dicom::pixeldata::PixelDecoder;
use tempfile::{tempdir, TempDir};

const HTJ2K_LOSSLESS_UID: &str = "1.2.840.10008.1.2.4.95";
const JPEG_XL_LOSSLESS_UID: &str = "1.2.840.10008.1.2.4.102";

#[test]
fn jpeg_ls_sample_attempts_decode() -> Result<()> {
    let Some(path) = fetch_test_file("pydicom/MR_small_jpeg_ls_lossless.dcm") else {
        return Ok(());
    };
    decode_or_assert_unsupported(&path)?;
    Ok(())
}

#[test]
fn jpeg2000_reversible_sample_attempts_decode() -> Result<()> {
    let Some(path) = fetch_test_file("pydicom/MR_small_jp2klossless.dcm") else {
        return Ok(());
    };
    decode_or_assert_unsupported(&path)?;
    Ok(())
}

#[test]
fn htj2k_and_jpegxl_report_clear_errors() -> Result<()> {
    let (_dir, htj2k_path) = write_stubbed_transfer_syntax(HTJ2K_LOSSLESS_UID, "HTJ2K");
    let err = open_file(&htj2k_path)
        .expect("open htj2k stub")
        .decode_pixel_data()
        .expect_err("HTJ2K should not decode without external codec support");
    assert_error_mentions_unsupported(&err);

    let (_dir, jxl_path) = write_stubbed_transfer_syntax(JPEG_XL_LOSSLESS_UID, "JPEGXL");
    let err = open_file(&jxl_path)
        .expect("open jpeg xl stub")
        .decode_pixel_data()
        .expect_err("JPEG-XL should not decode without external codec support");
    assert_error_mentions_unsupported(&err);

    Ok(())
}

fn fetch_test_file(name: &str) -> Option<std::path::PathBuf> {
    match dicom_test_files::path(name) {
        Ok(path) => Some(path),
        Err(err) => {
            eprintln!("Skipping {name} because it could not be fetched: {err:?}");
            None
        }
    }
}

fn decode_or_assert_unsupported(path: &std::path::Path) -> Result<()> {
    let obj = open_file(path)?;
    match obj.decode_pixel_data() {
        Ok(decoded) => {
            let stats = stats::pixel_statistics_from_decoded(&decoded)?;
            assert!(stats.total_pixels > 0);
        }
        Err(err) => assert_error_mentions_unsupported(&err),
    }
    Ok(())
}

fn write_stubbed_transfer_syntax(uid: &str, label: &str) -> (TempDir, std::path::PathBuf) {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join(format!("{label}_stub.dcm"));

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        Tag(0x0010, 0x0010),
        VR::PN,
        PrimitiveValue::from(format!("{label}^Codec")),
    ));
    obj.put(DataElement::new(
        tags::ROWS,
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    obj.put(DataElement::new(
        tags::COLUMNS,
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(vec![1_u8, 2, 3, 4]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(uid)
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.2001")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj
        .write_to_file(&path)
        .expect("write stubbed transfer syntax file");

    (dir, path)
}

fn assert_error_mentions_unsupported(err: &dicom::pixeldata::Error) {
    let msg = format!("{err:?}").to_lowercase();
    assert!(
        msg.contains("unsupported") || msg.contains("decoder"),
        "unexpected codec error message: {msg}"
    );
}

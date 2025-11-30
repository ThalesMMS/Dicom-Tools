//
// pixel_data_tests.rs
// Dicom-Tools-rs
//
// Tests for pixel data handling: decoding, encoding, multi-frame access, photometric interpretations.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::{open_file, FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::pixeldata::PixelDecoder;
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use tempfile::tempdir;

fn build_grayscale_dicom(
    rows: u16,
    cols: u16,
    bits_allocated: u16,
    bits_stored: u16,
    pixel_rep: u16,
    photometric: &str,
    pixels: Vec<u8>,
) -> (tempfile::TempDir, std::path::PathBuf) {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("grayscale.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Pixel^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(rows)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(cols)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(bits_allocated),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(bits_stored),
    ));
    obj.put(DataElement::new(
        tags::HIGH_BIT,
        VR::US,
        PrimitiveValue::from((bits_stored - 1) as u16),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(pixel_rep),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from(photometric),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.1"),
    ));

    let vr = if bits_allocated == 8 { VR::OB } else { VR::OW };
    obj.put(DataElement::new(tags::PIXEL_DATA, vr, PrimitiveValue::from(pixels)));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.1")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    (dir, path)
}

fn build_rgb_dicom(rows: u16, cols: u16, pixels: Vec<u8>) -> (tempfile::TempDir, std::path::PathBuf) {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("rgb.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("RGB^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(rows)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(cols)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(3_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(7_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("RGB"),
    ));
    obj.put(DataElement::new(
        tags::PLANAR_CONFIGURATION,
        VR::US,
        PrimitiveValue::from(0_u16), // Color-by-pixel
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.2"),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(pixels),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.2")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    (dir, path)
}

#[test]
fn decode_8bit_grayscale() {
    let pixels: Vec<u8> = vec![0, 64, 128, 192]; // 2x2 image
    let (_dir, path) = build_grayscale_dicom(2, 2, 8, 8, 0, "MONOCHROME2", pixels);

    let obj = open_file(&path).expect("open");
    let decoded = obj.decode_pixel_data().expect("decode");

    assert_eq!(decoded.rows(), 2);
    assert_eq!(decoded.columns(), 2);
    assert_eq!(decoded.bits_stored(), 8);
}

#[test]
fn decode_16bit_grayscale() {
    // 16-bit little-endian pixels
    let pixels: Vec<u8> = vec![
        0x00, 0x00, // 0
        0x00, 0x04, // 1024
        0x00, 0x08, // 2048
        0x00, 0x0C, // 3072
    ];
    let (_dir, path) = build_grayscale_dicom(2, 2, 16, 12, 0, "MONOCHROME2", pixels);

    let obj = open_file(&path).expect("open");
    let decoded = obj.decode_pixel_data().expect("decode");

    assert_eq!(decoded.bits_allocated(), 16);
    assert_eq!(decoded.bits_stored(), 12);
}

#[test]
fn decode_signed_pixels() {
    // Signed 16-bit pixels (CT data with negative values)
    let pixels: Vec<u8> = vec![
        0x00, 0xFC, // -1024 as i16 little-endian
        0x00, 0x00, // 0
        0x00, 0x04, // 1024
        0x00, 0x08, // 2048
    ];
    let (_dir, path) = build_grayscale_dicom(2, 2, 16, 12, 1, "MONOCHROME2", pixels);

    let obj = open_file(&path).expect("open");
    let decoded = obj.decode_pixel_data().expect("decode");

    assert_eq!(decoded.rows(), 2);
}

#[test]
fn decode_rgb_pixels() {
    // 2x2 RGB image (R, G, B for each pixel)
    let pixels: Vec<u8> = vec![
        255, 0, 0,   // Red
        0, 255, 0,   // Green
        0, 0, 255,   // Blue
        255, 255, 0, // Yellow
    ];
    let (_dir, path) = build_rgb_dicom(2, 2, pixels);

    let obj = open_file(&path).expect("open");
    let decoded = obj.decode_pixel_data().expect("decode");

    assert_eq!(decoded.rows(), 2);
    assert_eq!(decoded.columns(), 2);
    assert_eq!(decoded.samples_per_pixel(), 3);
}

#[test]
fn monochrome1_vs_monochrome2() {
    // MONOCHROME1: minimum pixel value = white
    // MONOCHROME2: minimum pixel value = black
    let pixels: Vec<u8> = vec![0, 255, 0, 255];

    let (_dir1, path1) = build_grayscale_dicom(2, 2, 8, 8, 0, "MONOCHROME1", pixels.clone());
    let (_dir2, path2) = build_grayscale_dicom(2, 2, 8, 8, 0, "MONOCHROME2", pixels);

    let obj1 = open_file(&path1).expect("open m1");
    let obj2 = open_file(&path2).expect("open m2");

    let pi1 = obj1
        .element(tags::PHOTOMETRIC_INTERPRETATION)
        .expect("pi")
        .to_str()
        .expect("str");
    let pi2 = obj2
        .element(tags::PHOTOMETRIC_INTERPRETATION)
        .expect("pi")
        .to_str()
        .expect("str");

    assert_eq!(pi1, "MONOCHROME1");
    assert_eq!(pi2, "MONOCHROME2");
}

#[test]
fn pixel_data_as_raw_bytes() {
    // Use even-length pixel data to avoid padding issues
    let pixels: Vec<u8> = vec![10, 20, 30, 40, 50, 60, 70, 80];
    let (_dir, path) = build_grayscale_dicom(2, 4, 8, 8, 0, "MONOCHROME2", pixels.clone());

    let obj = open_file(&path).expect("open");
    let pixel_elem = obj.element(tags::PIXEL_DATA).expect("pixel data");
    let raw_bytes = pixel_elem.to_bytes().expect("bytes");

    assert_eq!(raw_bytes.as_ref(), &pixels[..]);
}

#[test]
fn rescale_slope_intercept_presence() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("rescale.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Rescale^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(16_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(12_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(11_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        tags::RESCALE_SLOPE,
        VR::DS,
        PrimitiveValue::from("1.0"),
    ));
    obj.put(DataElement::new(
        tags::RESCALE_INTERCEPT,
        VR::DS,
        PrimitiveValue::from("-1024"),
    ));
    obj.put(DataElement::new(
        tags::RESCALE_TYPE,
        VR::LO,
        PrimitiveValue::from("HU"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.2"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.3"),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OW,
        PrimitiveValue::from(vec![0u8; 8]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.2")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.3")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let slope = read
        .element(tags::RESCALE_SLOPE)
        .expect("slope")
        .to_float64()
        .expect("f64");
    let intercept = read
        .element(tags::RESCALE_INTERCEPT)
        .expect("intercept")
        .to_float64()
        .expect("f64");

    assert!((slope - 1.0).abs() < 1e-6);
    assert!((intercept - (-1024.0)).abs() < 1e-6);
}

#[test]
fn window_center_width_application() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("window.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Window^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(7_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        tags::WINDOW_CENTER,
        VR::DS,
        PrimitiveValue::from([40.0_f64, 400.0]),
    ));
    obj.put(DataElement::new(
        tags::WINDOW_WIDTH,
        VR::DS,
        PrimitiveValue::from([80.0_f64, 1500.0]),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.4"),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(vec![0u8; 4]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.4")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let centers: Vec<f64> = read
        .element(tags::WINDOW_CENTER)
        .expect("wc")
        .to_multi_float64()
        .expect("f64s");
    let widths: Vec<f64> = read
        .element(tags::WINDOW_WIDTH)
        .expect("ww")
        .to_multi_float64()
        .expect("f64s");

    assert_eq!(centers.len(), 2);
    assert_eq!(widths.len(), 2);
    assert!((centers[0] - 40.0).abs() < 1e-6);
    assert!((widths[0] - 80.0).abs() < 1e-6);
}

#[test]
fn multiframe_pixel_data() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("multiframe.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("MultiFrame^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(
        tags::NUMBER_OF_FRAMES,
        VR::IS,
        PrimitiveValue::from("3"),
    ));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(7_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.5"),
    ));

    // 3 frames of 2x2 = 12 bytes
    let pixels: Vec<u8> = (0..12).collect();
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(pixels),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.5")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let frames = read
        .element(tags::NUMBER_OF_FRAMES)
        .expect("frames")
        .to_int::<i32>()
        .expect("i32");
    assert_eq!(frames, 3);

    let decoded = read.decode_pixel_data().expect("decode");
    assert_eq!(decoded.number_of_frames(), 3);
}

#[test]
fn bits_stored_less_than_allocated() {
    // Common scenario: 12-bit data in 16-bit allocation
    let pixels: Vec<u8> = vec![
        0xFF, 0x0F, // 4095 (max 12-bit)
        0x00, 0x08, // 2048
        0x00, 0x04, // 1024
        0x00, 0x00, // 0
    ];
    let (_dir, path) = build_grayscale_dicom(2, 2, 16, 12, 0, "MONOCHROME2", pixels);

    let obj = open_file(&path).expect("open");
    let decoded = obj.decode_pixel_data().expect("decode");

    assert_eq!(decoded.bits_allocated(), 16);
    assert_eq!(decoded.bits_stored(), 12);
}

#[test]
fn palette_color_tags() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("palette.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Palette^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(7_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("PALETTE COLOR"),
    ));

    // Palette descriptors (entries, first value, bits per entry)
    obj.put(DataElement::new(
        tags::RED_PALETTE_COLOR_LOOKUP_TABLE_DESCRIPTOR,
        VR::US,
        PrimitiveValue::from([256_u16, 0, 16]),
    ));
    obj.put(DataElement::new(
        tags::GREEN_PALETTE_COLOR_LOOKUP_TABLE_DESCRIPTOR,
        VR::US,
        PrimitiveValue::from([256_u16, 0, 16]),
    ));
    obj.put(DataElement::new(
        tags::BLUE_PALETTE_COLOR_LOOKUP_TABLE_DESCRIPTOR,
        VR::US,
        PrimitiveValue::from([256_u16, 0, 16]),
    ));

    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.6"),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(vec![0u8, 1, 2, 3]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.6")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let pi = read
        .element(tags::PHOTOMETRIC_INTERPRETATION)
        .expect("pi")
        .to_str()
        .expect("str");
    assert_eq!(pi, "PALETTE COLOR");
}

#[test]
fn ybr_photometric() {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("ybr.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("YBR^Test"),
    ));
    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(2_u16)));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(3_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(tags::HIGH_BIT, VR::US, PrimitiveValue::from(7_u16)));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("YBR_FULL"),
    ));
    obj.put(DataElement::new(
        tags::PLANAR_CONFIGURATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.pixel.7"),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(vec![128u8; 12]), // Y, Cb, Cr for 4 pixels
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.pixel.7")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(&path).expect("write");

    let read = open_file(&path).expect("read");
    let pi = read
        .element(tags::PHOTOMETRIC_INTERPRETATION)
        .expect("pi")
        .to_str()
        .expect("str");
    assert_eq!(pi, "YBR_FULL");
}

#[test]
fn pixel_data_size_validation() {
    // Use even-length pixel data (2x4 = 8 bytes)
    let pixels: Vec<u8> = vec![0, 1, 2, 3, 4, 5, 6, 7];
    let (_dir, path) = build_grayscale_dicom(2, 4, 8, 8, 0, "MONOCHROME2", pixels);

    let obj = open_file(&path).expect("open");
    let pixel_elem = obj.element(tags::PIXEL_DATA).expect("pixels");
    let bytes = pixel_elem.to_bytes().expect("bytes");

    // Expected size: rows * columns * (bits_allocated / 8) * samples_per_pixel = 2 * 4 * 1 * 1 = 8
    assert_eq!(bytes.len(), 8);
}
